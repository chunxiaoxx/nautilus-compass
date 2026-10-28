"""
Data Executor - Executes data processing tasks.
"""
import pandas as pd
import json
import jsonschema
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class DataExecutor:
    """
    Execute data processing tasks.

    Supports:
    - Data validation (JSON Schema)
    - Data quality checks
    - Data transformation
    """

    def __init__(self):
        """Initialize data executor."""
        logger.info("DataExecutor initialized")

    async def execute(self, state) -> str:
        """
        Execute data task.

        Args:
            state: Agent state with task information

        Returns:
            Execution result
        """
        logger.info(f"Executing data task {state.task_id}")

        # Parse input data
        try:
            data = json.loads(state.input_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON input: {e}")

        # Validate against expected schema (if it's a valid JSON Schema)
        if state.expected_output:
            try:
                schema = json.loads(state.expected_output)
                if isinstance(schema, dict) and ("type" in schema or "properties" in schema):
                    jsonschema.validate(instance=data, schema=schema)
                    logger.info("Data validation passed")
            except (json.JSONDecodeError, jsonschema.ValidationError) as e:
                logger.warning(f"Schema validation skipped or failed: {e}")

        # Perform data quality checks
        quality_report = await self.check_data_quality(data)

        # Return result
        result = {
            "data": data,
            "quality_report": quality_report,
            "status": "success"
        }

        return json.dumps(result, indent=2)

    async def check_data_quality(self, data: Any) -> Dict[str, Any]:
        """
        Check data quality.

        Args:
            data: Data to check

        Returns:
            Quality report
        """
        report = {
            "total_records": 0,
            "missing_values": 0,
            "duplicate_records": 0,
            "data_types": {}
        }

        # Convert to DataFrame if it's a list of dicts
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            df = pd.DataFrame(data)

            report["total_records"] = len(df)
            report["missing_values"] = df.isnull().sum().sum()
            report["duplicate_records"] = df.duplicated().sum()
            report["data_types"] = df.dtypes.astype(str).to_dict()

            # Calculate missing rate
            report["missing_rate"] = report["missing_values"] / (len(df) * len(df.columns)) if len(df) > 0 else 0

            # Calculate duplicate rate
            report["duplicate_rate"] = report["duplicate_records"] / len(df) if len(df) > 0 else 0

        return report

    async def validate_schema(self, data: Any, schema: Dict[str, Any]) -> bool:
        """
        Validate data against JSON schema.

        Args:
            data: Data to validate
            schema: JSON schema

        Returns:
            True if valid, False otherwise
        """
        try:
            jsonschema.validate(instance=data, schema=schema)
            return True
        except jsonschema.ValidationError:
            return False
