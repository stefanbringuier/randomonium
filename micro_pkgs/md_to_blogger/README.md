# Markdown To HTML for Blogger post

Although most have moved on from Blogger and its unfortunate that `markdown` is not a default editing mode, I'm too cautious to move to a new platform. Especially since I have no impact. The code here provides a quick way to convert common markdown to HTML for my Blogger site.


## Specifics
- There are some modifications to my Blogger site ([Dirac's Student](https://diracs-student.blogspot.com)) HTML template that are specified in this script.
- I use the code to both convert to HTML and upload to Blogger using Google's python API.
- All graphics are enconded using `base64`
- You need to setup your Google `Oauth2` and download a credentials json file to use the Blogger API.

## Usage
I can't guarentee this will work for others setups but the following steps may work:

1. `pip install -r requirements.txt`
2. Request crendentials for  [Oauth2 Blogger Google API](https://developers.google.com/blogger/docs/3.0/using). Download the credentials file.
3. Run via command line.
   ```shell
   usage: upload_post.py [-h] [--date DATE] [--draft DRAFT] infile outfile title client_secrets_file blogid

   Upload a blog post.

   positional arguments:
   infile               Input Markdown file
   outfile              Output HTML file
   title                Blog post title
   client_secrets_file  Client secrets file
   blogid		Blog ID
   
   optional arguments:
   -h, --help           show this help message and exit
   --date DATE          Publish date in any format (default: today's date)
   --draft DRAFT        Publish as draft or not


