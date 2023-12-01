from django.conf import settings
from django.core.files.base import ContentFile
from .models import KIModelPickleFile
import boto3
import pickle


def kimodell_von_pickle_file_aus_aws_bucket_laden(filepath='pickles/filename.pkl'):
    s3 = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    response = s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=filepath)
    body = response['Body'].read()
    kimodell = pickle.loads(body)
    return kimodell


def ki_modell_als_pickle_file_speichern(instanziertes_kimodel,
                                        name,
                                        filename,
                                        prognoseleistung_dict,
                                        ft_importance_list=None,
                                        ft_importance_list_merged=None):
    kimodel_pickle_file_obj, created = KIModelPickleFile.objects.get_or_create(name=name,
                                                                               defaults={'prognoseleistung_dict': prognoseleistung_dict,
                                                                                         'ft_importance_list': ft_importance_list,
                                                                                         'ft_importance_list_merged': ft_importance_list_merged})
    if not created:
        kimodel_pickle_file_obj.prognoseleistung_dict = prognoseleistung_dict
        if ft_importance_list:
            kimodel_pickle_file_obj.ft_importance_list = ft_importance_list
        if ft_importance_list_merged:
            kimodel_pickle_file_obj.ft_importance_list_merged = ft_importance_list_merged
        kimodel_pickle_file_obj.save()
    content = pickle.dumps(instanziertes_kimodel)
    content_file = ContentFile(content)
    kimodel_pickle_file_obj.file.save(filename, content_file)
    content_file.close()
