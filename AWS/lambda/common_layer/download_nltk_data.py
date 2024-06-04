import nltk

# Specify the download directory
nltk_data_dir = "/home/ec2-user/projects/styx/AWS/lambda/common_layer/python/nltk_data"

# Download the 'punkt' data
nltk.download("punkt", download_dir=nltk_data_dir)
