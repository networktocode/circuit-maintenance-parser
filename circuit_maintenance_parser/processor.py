"""Definition of Processor class."""
import logging
import traceback
import itertools

from typing import Iterable, Type, Dict, List

from pydantic import BaseModel, Extra
from pydantic.error_wrappers import ValidationError

from circuit_maintenance_parser.output import Maintenance
from circuit_maintenance_parser.data import NotificationData
from circuit_maintenance_parser.parser import Parser
from circuit_maintenance_parser.errors import ParsingError, ProcessorError, ProviderError


logger = logging.getLogger(__name__)


class GenericProcessor(BaseModel, extra=Extra.forbid):
    """Base class for the Processors."""

    # data_parsers contain the Parser Classes that will be tried
    data_parsers: List[Type[Parser]]

    # extended_data is custom default data from a Provider used to complement data from parsing
    extended_data: Dict = {}

    # maintenances_data is the variable that contains the result of the processor
    maintenances_data: List = []

    def _extend_processor_data(self, current_maintenance_data):
        """Method used to extend Maintenance data with some defaults."""
        current_maintenance_data["organizer"] = (
            self.extended_data.get("organizer")
            if "organizer" not in current_maintenance_data or current_maintenance_data["organizer"] == "None"
            else current_maintenance_data.get("organizer")
        )

        if "provider" not in current_maintenance_data:
            current_maintenance_data["provider"] = self.extended_data.get("provider")

    def _handle_extracted_data(self, maintenances_extracted_data: List):
        """Custom method per processor to accumulate the data from each DataPart."""
        raise NotImplementedError

    def _post_process(self):
        """Hook to add a post parsing process logic."""

    def run(self, data: NotificationData, extended_data: Dict) -> Iterable[Maintenance]:
        """Using the data_parsers, with a custom logic, will try to generate one or more Maintenances."""
        self.extended_data = extended_data

        some_parsing_happened = False
        for data_part, data_parser in itertools.product(data.get_data_parts(), self.data_parsers):
            if data_part.type in data_parser.get_data_types():
                some_parsing_happened = True
                try:
                    self._handle_extracted_data(data_parser().run(data_part.content))

                except (ParsingError, ValidationError) as exc:
                    parser_name = data_parser.__name__
                    processor_name = self.__class__.__name__
                    logger.debug(
                        "Parser %s for processor %s was not successful:\n%s",
                        parser_name,
                        processor_name,
                        traceback.format_exc(),
                    )
                    error_message = f"Parser class {parser_name} from {processor_name} failed due to: {exc.__cause__}\n"
                    raise ProcessorError(error_message) from exc

        if not some_parsing_happened:
            raise ProcessorError(
                "None of the supported parsers: "
                f"{', '.join([data_parser.__name__ for data_parser in self.data_parsers])} was matching any of the "
                f"provided data types: {', '.join([data_part.type for data_part in data.get_data_parts()])}."
            )

        self._post_process()

        return self.maintenances_data


class SimpleProcessor(GenericProcessor):
    """Processor to get all the Maintenance Data in each Data Part."""

    def _handle_extracted_data(self, maintenances_extracted_data):
        """For each data extracted, we try to build a Maintenance."""
        for extracted_data in maintenances_extracted_data:
            self._extend_processor_data(extracted_data)
            self.maintenances_data.append(Maintenance(**extracted_data))


class CombinedProcessor(GenericProcessor):
    """Processor for parse multiple DataParts to get a Maintenance notification."""

    combined_maintenance_data: Dict = {}

    def _handle_extracted_data(self, maintenances_extracted_data):
        """All the parsers contribute with a subset of data that is extended."""
        # We only expect one data object from these parsers
        if len(maintenances_extracted_data) == 1:
            self.combined_maintenance_data = {
                **self.combined_maintenance_data,
                **maintenances_extracted_data[0],
            }
        else:
            raise ParsingError(f"Unexpected data retrieved from parser: {maintenances_extracted_data}")

    def _post_process(self):
        """After processing all the parsers, we try to combine all the data together."""
        self._extend_processor_data(self.combined_maintenance_data)
        try:
            self.maintenances_data.append(Maintenance(**self.combined_maintenance_data))
        except ValidationError as exc:
            raise ProviderError("Not enough information available to create a Maintenance notification.") from exc
