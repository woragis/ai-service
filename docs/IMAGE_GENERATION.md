# Image Generation

## Overview

The AI service supports image generation using the Cipher (NoFilterGPT) provider. Generate images from text prompts with configurable parameters.

## Endpoint

```
POST /v1/images
```

## Request

```json
{
  "prompt": "A beautiful sunset over mountains",
  "provider": "cipher",
  "n": 1,
  "size": "1024x1024"
}
```

### Parameters

- **prompt** (required): Text description of the image to generate
- **provider** (optional): Currently only "cipher" is supported
- **n** (optional): Number of images to generate (default: 1)
- **size** (optional): Image size (default: "1024x1024")

### Supported Sizes

- `256x256`
- `512x512`
- `1024x1024`
- `1024x1792` (portrait)
- `1792x1024` (landscape)

## Response

```json
{
  "data": [
    {
      "url": "https://example.com/image.png"
    }
  ]
}
```

Or with base64:

```json
{
  "data": [
    {
      "b64_json": "iVBORw0KGgoAAAANSUhEUgAA..."
    }
  ]
}
```

## Configuration

### Environment Variables

```bash
CIPHER_API_KEY=your-api-key
CIPHER_IMAGE_URL=https://api.nofiltergpt.com/v1/images/generations
CIPHER_IMAGE_SIZE=1024x1024
CIPHER_IMAGE_N=1
```

## Usage Examples

### Generate Single Image

```bash
curl -X POST http://localhost:8000/v1/images \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A futuristic city at night"
  }'
```

### Generate Multiple Images

```bash
curl -X POST http://localhost:8000/v1/images \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A serene landscape",
    "n": 3,
    "size": "1024x1024"
  }'
```

### Custom Size

```bash
curl -X POST http://localhost:8000/v1/images \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A portrait photo",
    "size": "1024x1792"
  }'
```

## Python Example

```python
import httpx

response = httpx.post(
    "http://localhost:8000/v1/images",
    json={
        "prompt": "A beautiful sunset",
        "n": 1,
        "size": "1024x1024"
    }
)

data = response.json()
image_url = data["data"][0]["url"]
print(f"Image URL: {image_url}")
```

## Error Handling

### Provider Not Supported

```json
{
  "detail": "Only provider 'cipher' is supported for images currently"
}
```

### API Errors

```json
{
  "detail": "cipher image error: <error message>"
}
```

## Best Practices

1. **Use Descriptive Prompts** - More detail = better results
2. **Specify Style** - Include style keywords (e.g., "photorealistic", "anime", "oil painting")
3. **Set Appropriate Size** - Larger images take longer and cost more
4. **Handle Errors** - Always check for errors in response
5. **Cache Results** - Consider caching generated images

## Limitations

- Currently only Cipher provider is supported
- Rate limits apply (check provider documentation)
- Generation time varies (typically 10-30 seconds)
- Costs per image (check provider pricing)

## Future Enhancements

- Support for additional providers (OpenAI DALL-E, Stability AI)
- Image editing capabilities
- Image variation generation
- Style transfer

## Related Documentation

- [LLM Providers](./LLM_PROVIDERS.md)
- [Caching Policies](./CACHING_POLICIES.md)
- [Cost Control Policies](./COST_CONTROL.md)

