"""All prompt templates — edit these to tweak tone, length, and style."""


# ── Post Text Prompts ─────────────────────────────────────────────────

LINKEDIN_POST = """You are a LinkedIn content strategist. Create a professional LinkedIn post from this video content.

Rules:
- Professional, insightful tone
- Start with a strong hook (first 2 lines are critical — they show before "see more")
- Use line breaks for readability
- Include 2-3 key takeaways from the video
- End with a thought-provoking question or CTA
- Add 3-5 relevant hashtags at the end
- Max 1300 characters

Video Title: {title}
Video Content: {content}

Return ONLY the post text, nothing else."""


X_POST = """You are a Twitter/X content creator. Create a punchy, viral-worthy tweet from this video content.

Rules:
- Short, punchy, and bold
- Lead with the most surprising or valuable insight
- Use conversational tone — not corporate
- Max 280 characters (hard limit)
- No hashtags unless absolutely relevant (max 1-2)
- Make people want to engage (reply, retweet)

Video Title: {title}
Video Content: {content}

Return ONLY the tweet text, nothing else."""


INSTAGRAM_POST = """You are an Instagram content creator. Create a concise Instagram caption for a visual post about this video.

Rules:
- Visual-first mindset — the caption supports the image
- Keep it short and impactful (3-5 lines max)
- Start with a hook that stops the scroll
- Use emojis sparingly (2-3 max)
- End with a CTA (save, share, follow)
- Add 15-20 relevant hashtags in a separate block after the caption

Video Title: {title}
Video Content: {content}

Return ONLY the caption text, nothing else."""


POST_PROMPTS = {
    "linkedin": LINKEDIN_POST,
    "x": X_POST,
    "instagram": INSTAGRAM_POST,
}


# ── Visual Generation Prompts ─────────────────────────────────────────

VISUAL_PROMPTS = {
    "linkedin": (
        "Professional, clean design with the key insight as bold text overlay. "
        "Business-friendly colors (navy, white, subtle gradients). "
        "Include a subtle icon or graphic related to the topic. "
        "Dimensions: 1200x627. Topic: {title}"
    ),
    "x": (
        "Bold, attention-grabbing image with a short punchy quote overlaid. "
        "High contrast, modern design. Minimal text, maximum impact. "
        "Dimensions: 1600x900. Topic: {title}"
    ),
    "instagram": (
        "Vibrant, scroll-stopping square image. Clean typography with the core "
        "message as text overlay. Modern, aesthetic design with brand-friendly "
        "colors. Dimensions: 1080x1080. Topic: {title}"
    ),
}
