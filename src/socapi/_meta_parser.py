from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from __init__ import SocAPIClient

from typing import List, Literal, Union, Dict, Any, AnyStr
from http import HTTPMethod
import asyncio

from .models import _meta_parser_models as mpm
from .models import _client_model as cm

class MetaParser:

    @cm.validate_login
    async def get_blocks(
        self: "SocAPIClient",
        poll_id: int,
        includes: Union[Literal["all"], List[mpm.BlockIncludeField]] = "all"
    ):
        p = mpm.BlockPayload(poll_id=poll_id, includes=includes)

        r = await self._request(
            method=HTTPMethod.POST,
            endpoint=cm.Endpoints.BLOCKS_IN_POLL,
            payload=p.model_dump(),
            headers=self.headers,
            request_name=cm.RequestNames.BLOCKS_IN_POLL,
            extract_result=True,
        )

        return r


    @cm.validate_login
    async def get_questions(
        self: "SocAPIClient",
        parent_id: int,
        how: Literal["poll", "block"] | mpm.QuestionExportHow,
        includes: Union[Literal["all"], List[mpm.QuestionIncludeField]] = "all",
    ):
        p = mpm.QuestionsPayload(parent_id=parent_id, how=how, includes=includes)
        endpoint = mpm.QuestionEndpoints.get(p.how).value

        r = await self._request(
            method=HTTPMethod.POST,
            endpoint=endpoint,
            payload=p.model_dump(exclude={"how"}, exclude_none=True),
            headers=self.headers,
            request_name=cm.RequestNames.GET_QUESTIONS,
            extract_result = True,
        )

        return r


    @cm.validate_login
    async def get_metadata(self: "SocAPIClient", poll_id: int):
        result = await self._request(
            method=HTTPMethod.POST,
            endpoint=cm.Endpoints.POLL_DESCRIPTION_SOURCES,
            payload={"id": poll_id},
            headers=self.headers,
            request_name=cm.RequestNames.GET_METADATA,
            extract_result=True,
        )

        return result


    @cm.validate_login
    async def get_sources(self: "SocAPIClient", poll_id: int):
        result = await self._request(
            method=HTTPMethod.POST,
            endpoint=cm.Endpoints.POLL_DESCRIPTION_SOURCES,
            payload={"id": poll_id},
            headers=self.headers,
            request_name=cm.RequestNames.GET_METADATA,
            extract_result=True,
        )

        return result["sources"]




    async def map_question_ids(self: "SocAPIClient", poll_id: int) -> List[tuple[int, Any]]:
        blocks = await self.get_blocks(poll_id=poll_id)
        block_order_to_id = {b.get("order"): b.get("id") for b in blocks}

        get_block_questions_tasks = [
            self.get_questions(parent_id=block_order_to_id.get(o), how="block") for o in range(1, len(blocks)+1)
        ]

        ordered_questions = await asyncio.gather(*get_block_questions_tasks)

        mapped_questions = get_multiindex_from_questions(ordered_questions)

        return mapped_questions



def get_multiindex_from_questions(questions: List[List[Dict[str, Any]]])-> List[tuple[int, Any]]:

    def convert_technical_columns():
        return [
            ("CollectorNM", None, mpm.AnswerTypes.tech.value),
            ("respondent_id", None, mpm.AnswerTypes.tech.value),
            ("collector_id", None, mpm.AnswerTypes.tech.value),
            ("date_created", None, mpm.AnswerTypes.tech.value),
            ("date_modified", None, mpm.AnswerTypes.tech.value),
            ("survey_time", None, mpm.AnswerTypes.tech.value),
            ("ip_address", None, mpm.AnswerTypes.tech.value),
        ]

    def process_multicolumn_answer(answer: dict[str, Any], input_fields: list[tuple[int, Any, int]]):
        if answer["has_input"]:
            input_fields.append((answer["question_id"], answer["id"], mpm.AnswerTypes.input.value))

        return answer["question_id"], answer["id"], mpm.AnswerTypes.data.value

    def process_oe(question):
        return [(question["id"], None, mpm.AnswerTypes.input.value)]


    def process_single_column_question(question: dict[str, Any], input_fields: list[tuple[int, Any, int]]):
        for answer in question["answers"]:
            if answer["has_input"]:
                input_fields.append((answer["question_id"], answer["id"], mpm.AnswerTypes.input.value))

        return question["id"], None, mpm.AnswerTypes.data.value


    def convert_question_to_index(question_data: dict[str, Any]):
        input_fields = []

        match question_data["type_id"]:
            case mpm.QuestionTypes.multipunch.type_id | mpm.QuestionTypes.one_in_row.type_id | mpm.QuestionTypes.mult_in_row.type_id:
                processed_answers = [process_multicolumn_answer(a, input_fields) for a in question_data["answers"]]
                return processed_answers + input_fields

            case mpm.QuestionTypes.oe.type_id:
                return process_oe(question_data)

            case _ :
                processed_question = process_single_column_question(question_data, input_fields)
                return [processed_question] + input_fields

    res = convert_technical_columns() + [item for block in questions for question in block for item in convert_question_to_index(question)]

    return res
