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
from circuit_maintenance_parser.errors import ParserError, ProcessorError


logger = logging.getLogger(__name__)


class GenericProcessor(BaseModel, extra=Extra.forbid):
    """Base class for the Processors.

    Attributes:
        data_parsers: List of `Parsers` that will be used to parse the data when the data type matches. Each `Parser`
            will return a dictionary with extracted data, and depending on the logic, this will be used to create and
            return `Maintenances`
        extended_data (Optional): Dictionary containing information to complement the data extracted by the `Parsers`
            that is coming from the `Provider`
    """

    data_parsers: List[Type[Parser]]
    extended_data: Dict = {}

    def process(self, data: NotificationData, extended_data: Dict) -> Iterable[Maintenance]:
        """Method that uses the `data_parsers` to parse each `DataPart` from data.

        It also enriches the parsed data with `extended_data` in order to fulfill potential gaps that the
        notification data may have in order to create the `Maintenance` object.

        There are 2 hooks available, to be implemented by custom `Processors`:
            process_hook: Method that recieves the parsed output and manipulates the extracted data. It could create
                the final `Maintenances` or just accumulate them.
            post_process_hook (optional): Used to be able to do a final action on the extracted data before returing
                the final `Maintenances`.

        Attributes:
            data: A `NotificationData` object that contains multiple `DataPart` each one with a `type` and a `content`.
                This `type` is used to identify the candidate parsers, and then the `content` is parsed. This `data`
                can be initialized via multiple methods, such as simple object or from an email.
            extended_data (optional): It is a simple `dict` that the client can provide in order to extend some
                expected missing data from the notification in order to complete all the necessary `Maintenance`
                attributes.
        """
        self.extended_data = extended_data
        maintenances_data: List = []

        # First, we generate a list of tuples with a `DataPart` and `Parser` if the data type from the first is
        # supported by the second.
        data_part_and_parser_combinations = [
            (data_part, data_parser)
            for (data_part, data_parser) in itertools.product(data.data_parts, self.data_parsers)
            if data_part.type in data_parser.get_data_types()
        ]

        if not data_part_and_parser_combinations:
            error_message = (
                f"None of the supported parsers for processor {self.__class__.__name__} ("
                f"{', '.join([data_parser.__name__ for data_parser in self.data_parsers])}) was matching any of the "
                f"provided data types ({', '.join([data_part.type for data_part in data.data_parts])})."
            )

            logger.debug(error_message)
            raise ProcessorError(error_message)

        for data_part, data_parser in data_part_and_parser_combinations:
            try:
                self.process_hook(data_parser().parse(data_part.content), maintenances_data)

            except (ParserError, ValidationError) as exc:
                error_message = "Parser class %s from %s was not successful.\n%s"
                logger.debug(error_message, data_parser.__name__, self.__class__.__name__, traceback.format_exc())
                raise ProcessorError from exc

        self.post_process_hook(maintenances_data)

        return maintenances_data

    def process_hook(self, maintenances_extracted_data: List, maintenances_data: List):
        """Custom method per processor to accumulate the data from each DataPart."""
        raise NotImplementedError

    def post_process_hook(self, maintenances_data: List):
        """Hook to add a post parsing process logic."""

    def extend_processor_data(self, current_maintenance_data):
        """Method used to extend Maintenance data with some defaults."""
        temp_res = current_maintenance_data.copy()
        current_maintenance_data.update(self.extended_data)
        current_maintenance_data.update(temp_res)


class SimpleProcessor(GenericProcessor):
    """Processor to get all the Maintenance Data in each Data Part."""

    def process_hook(self, maintenances_extracted_data, maintenances_data):
        """For each data extracted (that can be multiple), we try to build a complete Maintenance."""
        for extracted_data in maintenances_extracted_data:
            self.extend_processor_data(extracted_data)
            maintenances_data.append(Maintenance(**extracted_data))


class CombinedProcessor(GenericProcessor):
    """Processor that combines the parsed output of multiple DataParts to get a single unified Maintenance notification."""

    # The CombinedProcessor will consolidate all the parsed data into this variable
    combined_maintenance_data: Dict = {}

    def process(self, data: NotificationData, extended_data: Dict) -> Iterable[Maintenance]:
        """Extend base class process method to ensure that self.combined_maintenance_data is initialized correctly."""
        self.combined_maintenance_data = {}
        return super().process(data, extended_data)

    def process_hook(self, maintenances_extracted_data, maintenances_data):
        """All the parsers contribute with a subset of data that is extended.

        For some notifications there can be multiple maintenances in a single file. To handle this, maintenances are store in a
        list where each of them can be extended with the extra processors.
        """
        if len(maintenances_extracted_data) == 1:
            self.combined_maintenance_data.update(maintenances_extracted_data[0])
        else:
            maintenances_data.extend(maintenances_extracted_data)

    def post_process_hook(self, maintenances_data):
        """After processing all the parsers, we try to combine all the data together."""
        self.extend_processor_data(self.combined_maintenance_data)
        if not maintenances_data:
            maintenances = [{}]
        else:
            maintenances = maintenances_data.copy()
            maintenances_data.clear()

        for maintenance in maintenances:
            try:
                combined_data = {**self.combined_maintenance_data, **maintenance}
                maintenances_data.append(Maintenance(**combined_data))
            except ValidationError as exc:
                raise ProcessorError("Not enough information available to create a Maintenance notification.") from exc
