import dataclasses
from typing import TypeVar

from mergenvision.domain import entities as domain
from mergenvision.infrastructure.database import models as orm

_T = TypeVar("_T")


def _map_to_domain(model: object, domain_cls: type[_T]) -> _T:
    kwargs: dict[str, object] = {}
    for field in dataclasses.fields(domain_cls):  # type: ignore[arg-type]
        value = getattr(model, field.name)
        kwargs[field.name] = value
    return domain_cls(**kwargs)


def map_person(model: orm.Person) -> domain.Person:
    return _map_to_domain(model, domain.Person)


def map_face_identity(model: orm.FaceIdentity) -> domain.FaceIdentity:
    return _map_to_domain(model, domain.FaceIdentity)


def map_process_record(model: orm.ProcessRecord) -> domain.ProcessRecord:
    return _map_to_domain(model, domain.ProcessRecord)


def map_inference_profile(model: orm.InferenceProfile) -> domain.InferenceProfile:
    return _map_to_domain(model, domain.InferenceProfile)


def map_person_photo(model: orm.PersonPhoto) -> domain.PersonPhoto:
    return _map_to_domain(model, domain.PersonPhoto)


def map_face_sample(model: orm.FaceSample) -> domain.FaceSample:
    return _map_to_domain(model, domain.FaceSample)


def map_recognition_result(model: orm.RecognitionResult) -> domain.RecognitionResult:
    return _map_to_domain(model, domain.RecognitionResult)


def map_process_event(model: orm.ProcessEvent) -> domain.ProcessEvent:
    return _map_to_domain(model, domain.ProcessEvent)
