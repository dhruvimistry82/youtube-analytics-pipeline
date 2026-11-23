
from airflow import DAG  # type: ignore[import-not-found]
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from api.video_stats import (
    get_playlist_id,
    get_video_ids,
    extract_video_data,
    save_data_to_json,
)

local_tz = ZoneInfo("America/New_York")

default_args = {
    "owner": "dataengineers",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "email": "dataengineers@example.com",
     "retries": 0,
    #"retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="produce_json",
    default_args=default_args,
    schedule_interval="0 14 * * *",
    start_date=datetime(2024, 6, 1, tzinfo=local_tz),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=1),
    tags=["youtube", "video_stats"],
) as dag:

    # Define tasks
    playlist_id = get_playlist_id()
    video_ids = get_video_ids(playlist_id)
    extracted_data = extract_video_data(video_ids)
    save_to_json_task = save_data_to_json(extracted_data)

    # Define task dependencies
    playlist_id >> video_ids >> extracted_data >> save_to_json_task
