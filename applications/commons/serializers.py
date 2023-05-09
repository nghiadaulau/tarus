from collections import OrderedDict
from io import BytesIO

import openpyxl
import pandas as pd
from django.db import models
from django.http import HttpResponse
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.utils.dataframe import dataframe_to_rows
from rest_framework import serializers


class BaseSerializer(serializers.Serializer):

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class CustomSerializerField(serializers.SerializerMethodField):
    def to_internal_value(self, data):
        return data

    def __init__(self, _field_name, **kwargs):
        self._field_name = _field_name
        super(CustomSerializerField, self).__init__(**kwargs)

    def to_representation(self, value):
        final_value = None
        if "__" in self._field_name:
            for name in self._field_name.split("__"):
                if not final_value:
                    final_value = getattr(value, name)
                else:
                    final_value = getattr(final_value, name)
        else:
            final_value = getattr(value, self._field_name)
        return final_value


class FactoryModelSerializer(object):
    def __init__(self, obj_model, extend_fields=None, exclude_fields=None, flat_json=False):
        self.obj_model = obj_model
        self.flat_json = flat_json
        self.declared_fields = []
        self.extend_fields = extend_fields
        self.exclude_fields = exclude_fields if exclude_fields else []
        self.serializer = self.get_serializer()

    def _get_declared_fields(self):
        if self.extend_fields:
            for field in self.extend_fields:
                self.declared_fields.append((field, CustomSerializerField(_field_name=field)))
        for field in self.obj_model._meta.fields:
            if isinstance(field, models.JSONField):
                self.declared_fields.append((field.name, CustomSerializerField(_field_name=field.name)))
            if field.name == "id":
                self.declared_fields.append((field.name, serializers.CharField(max_length=100)))
            if field.is_relation:
                self.declared_fields.append((field.name, CustomSerializerField(_field_name=f"{field.name}_id")))
            if hasattr(field, 'auto_now_add'):
                self.declared_fields.append((field.name, serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")))

    def get_serializer(self):
        self._get_declared_fields()

        class Base(object):
            pass

        Base._declared_fields = OrderedDict(self.declared_fields)

        class ModelsSerializer(Base, serializers.ModelSerializer):
            class Meta:
                model = self.obj_model
                fields = "__all__"

        return ModelsSerializer

    def get_json_data(self, qs, many=True):
        data = []
        if isinstance(qs, self.obj_model):
            if not many:
                data = self.serializer(qs).data
            else:
                data = [self.serializer(qs).data]
        else:
            data = self.serializer(qs, many=True).data
        return data

    def to_excel_download(self, qs):
        data = self.get_json_data(qs)
        new_data = []
        for obj in data:
            new_obj = {}
            for key, value in obj.items():
                if self.exclude_fields and key in self.exclude_fields:
                    continue
                if isinstance(value, (dict, OrderedDict)):
                    for k, v in value.items():
                        v = ILLEGAL_CHARACTERS_RE.sub('', str(v))
                        new_obj.update({k: v})
                else:
                    value = ILLEGAL_CHARACTERS_RE.sub('', str(value))
                    new_obj.update({key: value})
            new_data.append(new_obj)
        df = pd.DataFrame(new_data)
        book = openpyxl.Workbook()
        sheet = book.active
        for r in dataframe_to_rows(df, index=True, header=True):
            sheet.append(r)
        excel_file = BytesIO()
        book.save(excel_file)
        excel_file.seek(0)
        response = HttpResponse(excel_file.getvalue(),
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=data.xlsx'
        return response
