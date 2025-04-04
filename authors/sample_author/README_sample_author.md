# Sample Author Directory Structure

This directory provides a template for authors who want to contribute their content to the meGPT project. Follow this structure to organize your content effectively.

## Required Files

1. `published_content.csv` - Main index of all your published content with the following columns:
   - Kind: Type of content (e.g., book, blog, tweet, video)
   - SubKind: Optional subtype or platform (e.g., medium, blogger)
   - What: Title or description of the content
   - Where: Source location or platform
   - Published: Publication date
   - URL: Link to original content or file path

2. Content subdirectories (created as needed):
   - `medium_posts/` - Extracted text from Medium blog posts
   - `blogger_posts/` - Extracted text from Blogger posts
   - `twitter_conversations/` - Extracted conversations from Twitter
   - `books/` - PDF files of books or book chapters
   - `slides/` - Presentation slides
   - `videos/` - Video content references
   - `podcasts/` - Audio content references

## Example Structure

```
sample_author/
├── README_sample_author.md
├── published_content.csv
├── medium_posts/
│   └── sample_post.txt
├── blogger_posts/
│   └── sample_post.txt
├── twitter_conversations/
│   └── conversations.json
├── books/
│   └── sample_chapter.pdf
└── slides/
    └── sample_presentation.pdf
```

## Getting Started

1. Clone this repository
2. Create your author directory under `authors/`
3. Copy this sample structure
4. Add your `published_content.csv` file
5. Run the build script to process your content:
   ```
   python build.py your_author_name
   ```

## Content Guidelines

- Ensure all content is publicly shareable
- Include proper attribution and references
- Maintain consistent formatting in CSV files
- Use clear, descriptive titles in the 'What' field
- Include accurate publication dates
- Provide valid, accessible URLs 