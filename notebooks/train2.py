import argparse
import logging
import os
import torch

import evaluate
import numpy as np
from datasets import load_from_disk
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType

def print_trainable_parameters(model):
    """
    Prints the number of trainable parameters in the model.
    """
    trainable_params = 0
    all_param = 0
    for _, param in model.named_parameters():
        all_param += param.numel()
        if param.requires_grad:
            trainable_params += param.numel()
    print(
        f"trainable params: {trainable_params} || all params: {all_param} || trainable%: {100 * trainable_params / all_param}"
    )
    

def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    decoded_preds = tokenizer.batch_decode(predictions, skip_special_tokens=True)
    labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
    result = rouge.compute(predictions=decoded_preds, references=decoded_labels, use_stemmer=True)
    prediction_lens = [np.count_nonzero(pred != tokenizer.pad_token_id) for pred in predictions]
    result["gen_len"] = np.mean(prediction_lens)
    return {k: round(v, 4) for k, v in result.items()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # hyperparameters are passed as command-line arguments to the script.
    parser.add_argument("--model-name", type=str)

    parser.add_argument("--learning-rate", type=str, default=5e-5)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--train-batch-size", type=int, default=2)
    parser.add_argument("--eval-batch-size", type=int, default=8)
    parser.add_argument("--evaluation-strategy", type=str, default="epoch")
    parser.add_argument("--save-strategy", type=str, default="no")
    parser.add_argument("--save-steps", type=int, default=500)

    # # Data, model, and output directories
    # parser.add_argument("--output-data-dir", type=str, default=os.environ["SM_OUTPUT_DATA_DIR"])
    # parser.add_argument("--model-dir", type=str, default=os.environ["SM_MODEL_DIR"])
    # parser.add_argument("--train-dir", type=str, default=os.environ["SM_CHANNEL_TRAIN"])
    # parser.add_argument("--valid-dir", type=str, default=os.environ["SM_CHANNEL_VALID"])

    
    parser.add_argument("--output-data-dir", type=str, default="./output_data")
    parser.add_argument("--model-dir", type=str, default="./model")
    parser.add_argument("--train-dir", type=str, required=True)
    parser.add_argument("--valid-dir", type=str, required=True)

    args, _ = parser.parse_known_args()

    # Load metric
    rouge = evaluate.load("rouge")

    # load datasets
    train_dataset = load_from_disk(args.train_dir)
    valid_dataset = load_from_disk(args.valid_dir)

    logger = logging.getLogger(__name__)
    logger.info(f"training set: {train_dataset}")
    logger.info(f"validation set: {valid_dataset}")

    # download and quantize model from model hub
    bnb_config = BitsAndBytesConfig(
        load_in_8bit=True,
    )

    model = AutoModelForSeq2SeqLM.from_pretrained(args.model_name, quantization_config=bnb_config)
    model.gradient_checkpointing_enable()
    model = prepare_model_for_kbit_training(model)

    config = LoraConfig(
        r=16, 
        task_type=TaskType.SEQ_2_SEQ_LM,
        inference_mode=False
    )

    model = get_peft_model(model, config)
    print_trainable_parameters(model)
    
    # download the tokenizer too, which will be saved in the model artifact
    # and used at prediction time
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)

    # Check if CUDA is available
    use_fp16 = torch.cuda.is_available()

    # define training args
    training_args = Seq2SeqTrainingArguments(
        output_dir=args.model_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.train_batch_size,
        per_device_eval_batch_size=args.eval_batch_size,
        save_strategy=args.save_strategy,
        save_steps=args.save_steps,
        evaluation_strategy=args.evaluation_strategy,
        logging_dir=f"{args.output_data_dir}/logs",
        learning_rate=float(args.learning_rate),
        predict_with_generate=True,
        fp16=use_fp16,
    )

    # create trainer
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=valid_dataset,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    # train model
    trainer.train()

    # Saves the model to s3
    trainer.save_model(args.model_dir)
