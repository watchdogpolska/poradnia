from os.path import splitext
from django import template
from django.template.defaultfilters import stringfilter


register = template.Library()


@register.filter
@stringfilter
def file2css(path):
    """Converts a file into class name"""
    _ , ext = splitext(path);
    return {
        '.pdf' : 'fa fa-file-pdf-o',
        '.zip' : 'fa fa-file-archive-o',
        '.rar' : 'fa fa-file-archive-o',
        '.7z'  : 'fa fa-file-archive-o',
        '.tar' : 'fa fa-file-archive-o',
        '.gz'  : 'fa fa-file-archive-o',
        '.xlsx': 'fa fa-file-excel-o',
        '.xlsm': 'fa fa-file-excel-o',
        '.xlsb': 'fa fa-file-excel-o',
        '.xltx': 'fa fa-file-excel-o',
        '.xltm': 'fa fa-file-excel-o',
        '.xls' : 'fa fa-file-excel-o',
        '.xlt' : 'fa fa-file-excel-o',
        '.xlam': 'fa fa-file-excel-o',
        '.xlw' : 'fa fa-file-excel-o',
        '.csv' : 'fa fa-file-excel-o',
        '.dbf' : 'fa fa-file-excel-o',
        '.jpg' : 'fa fa-file-image-o',
        '.png' : 'fa fa-file-image-o',
        '.tiff': 'fa fa-file-image-o',
        '.gif' : 'fa fa-file-image-o',
        '.svg' : 'fa fa-file-image-o',
        '.cpp' : 'fa fa-file-code-o',
        '.js'  : 'fa fa-file-code-o',
        '.py'  : 'fa fa-file-code-o',
        '.html': 'fa fa-file-code-o',
        '.html': 'fa fa-file-code-o',
        '.rtf' : 'fa fa-file-word-o',
        '.doc' : 'fa fa-file-word-o',
        '.dot' : 'fa fa-file-word-o',
        '.docx': 'fa fa-file-word-o',
        '.docm': 'fa fa-file-word-o',
        '.dotx': 'fa fa-file-word-o',
        '.dotm': 'fa fa-file-word-o',
        '.docb': 'fa fa-file-word-o',
        '.docb': 'fa fa-file-word-o',
        '.odt' : 'fa fa-file-word-o',
        '.ott' : 'fa fa-file-word-o',
        '.oth' : 'fa fa-file-word-o',
        '.odm' : 'fa fa-file-word-o',
        '.odp' : 'fa fa-file-powerpoint-o',
        '.otp' : 'fa fa-file-powerpoint-o',
        '.odg' : 'fa fa-file-powerpoint-o',
        '.ppt' : 'fa fa-file-powerpoint-o',
        '.pot' : 'fa fa-file-powerpoint-o',
        '.mp3' : 'fa fa-file-audio-o',
        '.ogg' : 'fa fa-file-audio-o',
        '.oga' : 'fa fa-file-audio-o',
        '.wma' : 'fa fa-file-audio-o',
        '.wav' : 'fa fa-file-audio-o',
        '.m4a' : 'fa fa-file-audio-o',
        '.flac': 'fa fa-file-audio-o',
        '.acc' : 'fa fa-file-audio-o',
        '.txt' : 'fa fa-text-o',
        '.avi' : 'fa fa-video-o',
        '.mp4' : 'fa fa-video-o',
        '.webm': 'fa fa-video-o',
    }.get(ext, 'fa fa-file-o')
