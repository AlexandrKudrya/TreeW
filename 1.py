from tinytag import TinyTag
tag = TinyTag.get('static/img/questions/16.mp4')
print('This track is by %s.' % tag.artist)
print('It is %f seconds long.' % tag.duration)