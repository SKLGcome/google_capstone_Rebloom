"""회복 유형 코드와 진단 축 설명을 제공한다."""

RECOVERY_TYPES = (
    "REP",
    "RED",
    "RCP",
    "RCD",
    "AEP",
    "AED",
    "ACP",
    "ACD",
)

_ENERGY_DESCRIPTIONS = {
    "A": "신체적·정서적 에너지 수준이 비교적 높음",
    "R": "신체적·정서적 에너지 수준이 낮음",
}

_DIRECTION_DESCRIPTIONS = {
    "C": "진로와 목표가 비교적 명확함",
    "E": "진로와 목표가 아직 불명확함",
}

_ACTION_DESCRIPTIONS = {
    "D": "생각을 실제 행동으로 옮기는 정도가 비교적 높음",
    "P": "생각을 실제 행동으로 옮기는 데 어려움이 있음",
}


def normalize_recovery_type(recovery_type: str) -> str:
    """회복 유형 코드를 정규화하고 지원하는 코드인지 검증한다."""

    normalized_type = recovery_type.strip().upper()
    if normalized_type not in RECOVERY_TYPES:
        raise ValueError(f"Unknown recovery type: {recovery_type}")
    return normalized_type


def describe_recovery_type(recovery_type: str) -> str:
    """세 진단 축을 사람이 이해할 수 있는 설명으로 변환한다."""

    normalized_type = normalize_recovery_type(recovery_type)
    return (
        f"- 에너지: {_ENERGY_DESCRIPTIONS[normalized_type[0]]}\n"
        f"- 방향성: {_DIRECTION_DESCRIPTIONS[normalized_type[1]]}\n"
        f"- 행동: {_ACTION_DESCRIPTIONS[normalized_type[2]]}"
    )
