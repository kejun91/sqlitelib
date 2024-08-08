import traceback


def split_list_into_batches(original_list, list_size):
    return [original_list[i:i + list_size] for i in range(0, len(original_list), list_size)]

def get_exception_detail(e: Exception):
    return [f"{e.__class__.__module__}.{e.__class__.__name__}: {e}"] + traceback.format_list(traceback.extract_tb(e.__traceback__))