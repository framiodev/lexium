import os,glob,sys
from PIL import Image
a='android/app/src/main/res'
src=Image.open('tools/icon-1024.png').convert('RGB')
sizes={'mdpi':48,'hdpi':72,'xhdpi':96,'xxhdpi':144,'xxxhdpi':192}
for d,n in sizes.items():
    for name in ('ic_launcher.png','ic_launcher_round.png','ic_launcher_foreground.png'):
        p=f'{a}/mipmap-{d}/{name}'
        if os.path.exists(os.path.dirname(p)): src.resize((n,n),Image.LANCZOS).save(p)
for f in glob.glob(f'{a}/mipmap-anydpi-v26/*.xml'): os.remove(f)
g='android/app/build.gradle'
t=open(g).read()
run=os.environ.get('GITHUB_RUN_NUMBER','1')
t=t.replace('versionCode 1','versionCode '+run)
t+='''
android {
    signingConfigs { icinde { storeFile file('../../icinde.keystore'); storePassword 'icinde123'; keyAlias 'icinde'; keyPassword 'icinde123' } }
    buildTypes { release { signingConfig signingConfigs.icinde } }
}
'''
open(g,'w').write(t)
