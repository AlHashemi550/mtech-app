with open('app.py', 'r') as f:
    content = f.read()
if 'os.environ.get' not in content:
    content = content.replace('app.run(', "port = int(os.environ.get('PORT', 5000))\napp.run(host='0.0.0.0', port=port, ")
    with open('app.py', 'w') as f:
        f.write(content)
    print('Done! PORT added.')
else:
    print('Already OK!')
