from storage_for_resolutions_and_sizes import load_resolution_data

data = load_resolution_data()

for course, semesters in data.items():
        for semester, subjects in semesters.items():
            for subject, videos in subjects.items():
                for video_title, formats in videos.items():
                    for fmt in formats:
                        if fmt["filesize_mb"] < 30:
                            print(video_title, subject)
