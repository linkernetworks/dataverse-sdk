import re
from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, validator

from ..exceptions.client import ClientConnectionError
from .common import (
    AnnotationFormat,
    AttributeType,
    DatasetStatus,
    DatasetType,
    OntologyImageType,
    OntologyPcdType,
    SensorType,
)


class AttributeOption(BaseModel):
    id: Optional[int] = None
    value: Union[str, float, int, bool]


class Attribute(BaseModel):
    id: Optional[int] = None
    name: str
    options: Optional[list[AttributeOption]] = None
    type: AttributeType

    class Config:
        use_enum_values = True

    @validator("type")
    def option_data_validator(cls, value, values, **kwargs):
        if value == AttributeType.OPTION and not values.get("options"):
            raise ValueError(
                "Need to assign value for `options` "
                + "if the Attribute type is option"
            )
        return value


class Sensor(BaseModel):
    id: Optional[int] = None
    name: str
    type: SensorType

    class Config:
        use_enum_values = True


class OntologyClass(BaseModel):
    id: Optional[int] = None
    name: str
    color: str
    rank: int
    attributes: Optional[list[Attribute]] = None

    @validator("color", each_item=True)
    def color_validator(cls, value):
        if not value.startswith("#") or not re.search(
            r"\b[a-zA-Z0-9]{6}\b", value.lstrip("#")
        ):
            raise ValueError(
                f"Color field needs starts with `#` and has 6 digits behind it, get : {value}"
            )
        return value


class Ontology(BaseModel):
    id: Optional[int] = None
    name: str
    image_type: Optional[OntologyImageType] = None
    pcd_type: Optional[OntologyPcdType] = None
    classes: Optional[list[OntologyClass]] = None

    class Config:
        use_enum_values = True


class DataSource(str, Enum):

    Azure = "azure"
    AWS = "aws"
    SDK = "sdk"


class DataConfig(BaseModel):
    storage_url: str
    container_name: Optional[str]
    sas_token: Optional[str]
    data_folder: str
    sequential: bool
    generate_metadata: bool
    description: Optional[str]
    type: str
    annotation_format: str

    class Config:
        extra = "allow"


class Project(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    ego_car: Optional[str] = None
    ontology: Ontology
    sensors: list[Sensor]

    def create_dataset(
        self,
        name: str,
        data_source: DataSource,
        sensors: list[Sensor],
        type: DatasetType,
        annotation_format: AnnotationFormat,
        storage_url: str,
        data_folder: str,
        container_name: Optional[str] = None,
        sas_token: Optional[str] = None,
        sequential: bool = False,
        generate_metadata: bool = False,
        description: Optional[str] = None,
    ):
        try:
            import config

            client = config._client
        except Exception as e:
            raise ClientConnectionError(f"Failed to get client info: {e}")
        dataset_output = client.create_dataset(
            name=name,
            data_source=data_source,
            project=self,
            sensors=sensors,
            type=type,
            annotation_format=annotation_format,
            storage_url=storage_url,
            container_name=container_name,
            data_folder=data_folder,
            sas_token=sas_token,
            sequential=sequential,
            generate_metadata=generate_metadata,
            description=description,
        )
        return dataset_output


class Dataset(BaseModel):
    id: Optional[int] = None
    project: Project
    sensors: list[Sensor]
    name: str
    type: DatasetType
    data_source: DataSource
    annotation_format: AnnotationFormat
    status: DatasetStatus
    sequential: bool = False
    generate_metadata: bool = False
    description: Optional[str] = None
    file_count: Optional[int] = None
    image_count: Optional[int] = None
    pcd_count: Optional[int] = None
    created_by: Optional[int] = None
    container_name: Optional[str] = None
    storage_url: Optional[str] = None

    class Config:
        extra = "allow"
