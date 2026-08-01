from litellm.integrations.custom_logger import CustomLogger

class StripImageUrl(CustomLogger):
    async def async_post_call_success_hook(self, data, user_api_key_dict, response):
        if not hasattr(response, "data") or not response.data:
            return response

        try:
            for item in response.data:
                if isinstance(item, dict):
                    item.pop("url", None)
                elif hasattr(item, "url"):
                    try:
                        delattr(item, "url")
                    except Exception:
                        if hasattr(item, "__dict__"):
                            item.__dict__.pop("url", None)
        except Exception:
            pass

        return response

# IMPORTANT: LiteLLM expects an instance with this exact name style
strip_image_url = StripImageUrl()
