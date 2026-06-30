import unittest
from unittest.mock import patch

from dynamic_fas.conversation import handle_chat
from dynamic_fas.message_router import MessageRoute
from dynamic_fas.models import DynamicChatRequest
from dynamic_fas.session_store import reset_session


QUESTIONS = [
    {
        "question_id": 101,
        "question_text": "Mô tả hoàn cảnh tài chính của gia đình.",
        "is_required": True,
    },
    {
        "question_id": 102,
        "question_text": "Bạn có thông tin bổ sung nào không?",
        "is_required": False,
    },
]


def make_request(message: str, current_answers=None) -> DynamicChatRequest:
    return DynamicChatRequest(
        session_id="test-session",
        fas_scheme_id=10,
        message=message,
        questions=QUESTIONS,
        current_answers=current_answers or {},
    )


class DynamicFasConversationTests(unittest.TestCase):
    def setUp(self):
        reset_session("test-session")

    @patch("dynamic_fas.conversation.extract_answers")
    @patch("dynamic_fas.conversation.route_message")
    def test_new_answer_becomes_suggestion(self, route, extract):
        route.return_value = MessageRoute(category="FORM_FILLING")
        extract.return_value = {"101": "Gia đình vừa bị giảm thu nhập."}

        response = handle_chat(make_request("Gia đình tôi bị giảm thu nhập"))

        self.assertEqual(
            response.suggested_fields["101"],
            "Gia đình vừa bị giảm thu nhập.",
        )
        self.assertEqual(response.progress.completed, 1)
        self.assertEqual(response.progress.total, 1)

    @patch("dynamic_fas.conversation.extract_answers")
    @patch("dynamic_fas.conversation.route_message")
    def test_changed_answer_requires_confirmation(self, route, extract):
        route.return_value = MessageRoute(category="FORM_FILLING")
        extract.return_value = {"101": "Bố vừa mất việc."}

        response = handle_chat(
            make_request(
                "Thực ra bố tôi vừa mất việc",
                current_answers={"101": "Thu nhập bị giảm."},
            )
        )

        field = response.assistant_state.questions["101"]
        self.assertEqual(field.value, "Thu nhập bị giảm.")
        self.assertEqual(field.pending_value, "Bố vừa mất việc.")
        self.assertEqual(field.status, "pending_update")
        self.assertNotIn("101", response.suggested_fields)

    @patch("dynamic_fas.conversation.extract_answers")
    @patch("dynamic_fas.conversation.route_message")
    def test_user_can_accept_pending_update(self, route, extract):
        route.return_value = MessageRoute(category="FORM_FILLING")
        extract.return_value = {"101": "Bố vừa mất việc."}
        handle_chat(
            make_request(
                "Thực ra bố tôi vừa mất việc",
                current_answers={"101": "Thu nhập bị giảm."},
            )
        )

        response = handle_chat(
            make_request("Có", current_answers={"101": "Thu nhập bị giảm."})
        )

        self.assertEqual(response.suggested_fields["101"], "Bố vừa mất việc.")
        self.assertIsNone(response.assistant_state.questions["101"].pending_value)

    @patch("dynamic_fas.conversation.extract_answers")
    @patch("dynamic_fas.conversation.route_message")
    def test_user_can_reject_pending_update(self, route, extract):
        route.return_value = MessageRoute(category="FORM_FILLING")
        extract.return_value = {"101": "Bố vừa mất việc."}
        handle_chat(
            make_request(
                "Thực ra bố tôi vừa mất việc",
                current_answers={"101": "Thu nhập bị giảm."},
            )
        )

        response = handle_chat(
            make_request("Không", current_answers={"101": "Thu nhập bị giảm."})
        )

        field = response.assistant_state.questions["101"]
        self.assertEqual(field.value, "Thu nhập bị giảm.")
        self.assertIsNone(field.pending_value)
        self.assertEqual(response.suggested_fields, {})

    @patch("dynamic_fas.conversation.extract_answers")
    @patch("dynamic_fas.conversation.route_message")
    def test_unknown_question_id_is_ignored(self, route, extract):
        route.return_value = MessageRoute(category="FORM_FILLING")
        extract.return_value = {"999": "Unknown answer"}

        response = handle_chat(make_request("Some information"))

        self.assertEqual(response.suggested_fields, {})
        self.assertNotIn("999", response.assistant_state.questions)

    @patch("dynamic_fas.conversation.extract_answers")
    @patch("dynamic_fas.conversation.route_message")
    def test_multiple_updates_are_confirmed_one_at_a_time(self, route, extract):
        route.return_value = MessageRoute(category="FORM_FILLING")
        extract.return_value = {
            "101": "Hoàn cảnh mới.",
            "102": "Thông tin mới.",
        }
        current_answers = {
            "101": "Hoàn cảnh cũ.",
            "102": "Thông tin cũ.",
        }
        handle_chat(make_request("Tôi muốn sửa cả hai", current_answers))

        first_confirmation = handle_chat(make_request("Có", current_answers))
        self.assertEqual(first_confirmation.suggested_fields["101"], "Hoàn cảnh mới.")
        self.assertEqual(
            first_confirmation.assistant_state.pending_update_question_id,
            102,
        )

        second_confirmation = handle_chat(make_request("Có", current_answers))
        self.assertEqual(
            second_confirmation.suggested_fields,
            {"101": "Hoàn cảnh mới.", "102": "Thông tin mới."},
        )

    def test_scheme_without_questions_returns_safe_reply(self):
        request = DynamicChatRequest(
            session_id="test-session",
            fas_scheme_id=10,
            message="Xin chào",
            questions=[],
            current_answers={},
        )

        response = handle_chat(request)

        self.assertEqual(response.progress.total, 0)
        self.assertEqual(response.suggested_fields, {})
        self.assertIn("does not currently have any additional questions", response.reply)


if __name__ == "__main__":
    unittest.main()
