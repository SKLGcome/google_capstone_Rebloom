import unittest

from api.tools import build_result_tool


class BuildResultToolTest(unittest.TestCase):
    def test_build_result_tool_returns_expected_payload(self):
        result = build_result_tool(
            recovery_type="REP",
            summary="무기력과 진로 불확실성이 함께 나타나는 상태",
            mission="작은 목표 세우기",
            next_step="정서적 회복 시작",
        )

        self.assertEqual(
            result,
            {
                "recovery_type": "REP",
                "summary": "무기력과 진로 불확실성이 함께 나타나는 상태",
                "mission": "작은 목표 세우기",
                "next_step": "정서적 회복 시작",
            },
        )


if __name__ == "__main__":
    unittest.main()
