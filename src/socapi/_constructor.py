from typing import TYPE_CHECKING, List,Optional
from datetime import datetime

if TYPE_CHECKING:
    from __init__ import SocAPIClient

import asyncio

from . import utils
from .models import _client_model as cm
from .models import _general_models as gm

from pydantic import validate_call
from http import HTTPMethod

class Constructor:
    """
    A class to handle creating and modifying poll questions from a socpanel API.

    Expects the main class to define:
    - self._headers: headers for requests.
    - self._login(): method to login in panel.
    - self._request(): method to send generic requests.

    Attributes:
    -----------
    headers : dict
        Headers for the API requests.

    Methods:
    --------

    """


    @cm.validate_login
    @validate_call
    async def duplicate_poll(
            self,
            id: int,
            with_counters: bool
    ) -> gm.Poll:
        if TYPE_CHECKING:
            self: SocAPIClient

        result = await self._request(
            method=HTTPMethod.POST,
            endpoint=cm.Endpoints.DUPLICATE_POLL,
            payload={
                "id": id,
                "with_counters": with_counters,
            },
            headers=self.headers,
            request_name=cm.RequestNames.DUPLICATE_POLL,
            extract_result=True,
        )

        return gm.Poll(**result)


    @cm.validate_login
    @validate_call
    async def update_meta(
            self,
            id: int,
            meta: List[int]
    ) -> None:
        if TYPE_CHECKING:
            self: SocAPIClient
        await self._request(
            method=HTTPMethod.POST,
            endpoint=cm.Endpoints.UPDATE_META,
            payload={
                "id": id,
                "meta": meta,
            },
            headers=self.headers,
            request_name=cm.RequestNames.UPDATE_META,
        )


    @cm.validate_login
    @validate_call
    async def create_question(
            self,

            title: str,
            measure: gm.Measures,
            type_id: gm.AnswerTypes,
            max_answer: int,
            min_answer: int,
            order: int,
            block_id: int,
            optional: bool,
            has_input: bool,
            randomized: bool,
            transpose: bool,
            display_labels: bool,
            children_randomized: bool,
            is_panel: bool,

            answers: Optional[List[gm.Answer]] = None,
            children: Optional[List[gm.Question]] = None,
    ) -> gm.Question:

        # implement children logic

        if TYPE_CHECKING:
            self: SocAPIClient

        question = gm.Question(
            title=title,
            measure=measure,
            type_id=type_id,
            max_answer=max_answer,
            min_answer=min_answer,
            order=order,
            block_id=block_id,
            optional=optional,
            has_input=has_input,
            randomized=randomized,
            transpose=transpose,
            display_labels=display_labels,
            children_randomized=children_randomized,
            is_panel=is_panel,
            answers=answers,
            children=children,
        )

        result = await self._request(
            method=HTTPMethod.POST,
            endpoint=cm.Endpoints.QUESTION_CREATE,
            payload=question.model_dump(mode="json", exclude={"created_at"}, exclude_none=True),
            headers=self.headers,
            request_name=cm.RequestNames.QUESTION_CREATE,
            extract_result=True,
        )

        return gm.Question(**result)

    @cm.validate_login
    @validate_call
    async def edit_question(
            self,

            title: str,
            id: int,
            parent_id: int,
            measure: gm.Measures,
            type_id: gm.AnswerTypes,
            max_answer: int,
            min_answer: int,
            order: int,

            block_id: int,
            optional: bool,
            has_input: bool,

            randomized: bool,
            transpose: bool,
            display_labels: bool,
            children_randomized: bool,
            is_panel: bool,
            created_at: datetime,

            status_id: int = 1,
            answer_type: str = "",
            condition_type: str = "",
            input_validation: str = "",

            children: Optional[List[gm.Question]] = None
    ) -> gm.Question:

        # implement children logic

        if TYPE_CHECKING:
            self: SocAPIClient

        question = gm.Question(
            id=id,
            parent_id=parent_id,
            title=title,
            measure=measure,
            type_id=type_id,
            max_answer=max_answer,
            min_answer=min_answer,
            order=order,
            block_id=block_id,
            optional=optional,
            has_input=has_input,
            randomized=randomized,
            transpose=transpose,
            display_labels=display_labels,
            children_randomized=children_randomized,
            is_panel=is_panel,
            created_at=created_at,
            status_id=status_id,
            answer_type=answer_type,
            condition_type=condition_type,
            input_validation=input_validation,
            children=children,
        )

        result = await self._request(
            method=HTTPMethod.POST,
            endpoint=cm.Endpoints.QUESTION_UPDATE,
            payload=question.model_dump(mode="json", exclude={"updated_at"}, exclude_none=True),
            headers=self.headers,
            request_name=cm.RequestNames.QUESTION_UPDATE,
            extract_result=True,
        )

        return gm.Question(**result)

    @cm.validate_login
    @validate_call
    async def create_answer(
            self,

            order: int,
            title: str,
            has_input: bool,
            skip_randomize: bool,
            exclude_answer: bool,
            optional: bool,
            question_id: int,
            input_validation: gm.InputValidations,
            is_panel: bool
    ) -> gm.Answer:
        if TYPE_CHECKING:
            self: SocAPIClient

        answer = gm.Answer(
            order=order,
            title=title,
            has_input=has_input,
            skip_randomize=skip_randomize,
            exclude_answer=exclude_answer,
            optional=optional,
            question_id=question_id,
            input_validation=input_validation,
            is_panel=is_panel,
        )

        result = await self._request(
            method=HTTPMethod.POST,
            endpoint=cm.Endpoints.ANSWER_CREATE,
            payload=answer.model_dump(mode="json", exclude={"created_at"}, exclude_none=True),
            headers=self.headers,
            request_name=cm.RequestNames.ANSWER_CREATE,
            extract_result=True,
        )

        return gm.Answer(**result)
