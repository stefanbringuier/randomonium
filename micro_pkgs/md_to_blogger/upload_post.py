import argparse
import datetime
import os
import pickle
import sys
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import md_to_html

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/blogger']

def get_credentials(token_file, client_secrets_file):
    creds = None
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
    return creds

def upload_blog_post(html_file, title, pub_date, blog_id, client_secrets_file, token_file, draft=True):
    # Get valid credentials
    credentials = get_credentials(token_file, client_secrets_file)

    # Create a service object
    service = build('blogger', 'v3', credentials=credentials)

    # Read the HTML file.
    with open(html_file, 'r') as f:
        html_content = f.read()

    # Create a new post object.
    post = {
        'title' : title,
        'content': html_content,
    }

    # Call the `insert` method of the `BlogPosts` service to insert the post into your blog.
    if draft:
        response = service.posts().insert(blogId=blog_id,isDraft=True,body=post).execute()
    else:
        response = service.posts().publish(blogId=blog_id,publishDate=pub_date,body=post).execute()

    # Print the ID of the inserted post.
    print('Post ID:', response['id'])

def main():
    parser = argparse.ArgumentParser(description='Upload a blog post.')
    parser.add_argument('infile', help='Input Markdown file')
    parser.add_argument('outfile', help='Output HTML file')
    parser.add_argument('title', help='Blog post title')
    parser.add_argument('client_secrets_file', help='Client secrets file')
    parser.add_argument('blogid', default='0000000000000000000', help='Blog ID')
    parser.add_argument('--date', default=datetime.datetime.now().strftime('%A, %B %d, %Y'),
                        help='Publish date in any format (default: today\'s date)')
    parser.add_argument('--draft', default=True, type=bool, help='Publish as draft or not')
    args = parser.parse_args()

    # Parse date and convert it to the required format
    parsed_date = datetime.datetime.strptime(args.date, '%A, %B %d, %Y')
    formatted_date = parsed_date.strftime('%A, %B %d, %Y')

    html = md_to_html.process(args.infile)
    with open(args.outfile, 'w') as f:
        f.write(html)

    upload_blog_post(args.outfile, args.title, formatted_date, args.blogid, args.client_secrets_file, 'token.pickle', args.draft)

if __name__ == '__main__':
    main()
