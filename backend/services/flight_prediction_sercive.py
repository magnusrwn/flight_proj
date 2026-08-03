from src.models.base_models import AviationApiResponse, SendFlightRequest
from src.utils import is_in_table_
import logging

logger = logging.getLogger(__name__)

def predict_flight__service(body:SendFlightRequest) -> AviationApiResponse:
    logger.info("%(asctime)s -- FUNC:send_flight__service -- ",) # NOTE: Finish log
    in_in_table_resp = is_in_table_(
        table_name="airport_data",
        column="code",
        airprot_code=body.depIataCode
    )
    # handle
    # in_in_table_resp

    return AviationApiResponse(
        data = {}
    )