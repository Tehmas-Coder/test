from django.forms.models import model_to_dict


def create_seed_from_db(model):
    """
    Creates a seed list from all objects of a given model.

    Args:
        model: A Django model.

    Returns:
        A list of dictionaries representing the seed data.
    """

    objects = model.objects.all()
    seed = []
    for row in objects:
        one_seed = {
            "model": "system_admin." + model.__name__,
            "pk": row.pk,
        }

        model_dict = model_to_dict(row)

        model_dict["created_at"] = "1995-07-27T00:00:00Z"
        model_dict["updated_at"] = "1995-07-27T00:00:00Z"

        del model_dict["created_by"]
        del model_dict["updated_by"]
        del model_dict["meta_status"]

        one_seed["fields"] = model_dict

        seed.append(one_seed)

    return seed
