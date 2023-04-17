It might look like leftover trash, but this is actually a necessary folder in case

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

fails.

It fails on my work laptop, but it works on my computer at home and i dont know why, so im leaving the folder with the code.