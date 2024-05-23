import backoff
import requests
from styx_packages.styx_logger.logging_config import setup_logger

logger = setup_logger(__name__)


def make_request(url, method="get", **kwargs):
    @backoff.on_exception(
        backoff.expo,
        requests.exceptions.RequestException,
        max_tries=8,
        giveup=lambda e: e.response is not None and e.response.status_code < 500,
        on_backoff=lambda details: logger.warning(
            f"Retrying due to {details['exception']}. Attempt {details['tries']}"
        ),
        on_giveup=lambda details: logger.error(
            f"Giving up due to {details['exception']} after {details['tries']} attempts"
        ),
        on_success=lambda details: logger.info(
            f"Request succeeded after {details['tries']} attempts"
        ),
    )
    def _request_with_backoff():
        with requests.Session() as session:
            if method.lower() == "get":
                response = session.get(url, **kwargs)
            elif method.lower() == "post":
                response = session.post(url, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            response.raise_for_status()
            return response

    # Call the inner function which is decorated with backoff
    return _request_with_backoff()
