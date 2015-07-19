import os
import sys
import commands
import pipes
import xml.etree.ElementTree as ET
import plistlib
import StringIO

def shellquote(s):
    return pipes.quote(s)



scriptPath = os.path.split(os.path.realpath(__file__))[0] + '/'
removePIEPath = scriptPath + 'removePIEOSX'
entitlementXML = scriptPath + 'iPhoneEntitlement.xml'
entitlementPlist = scriptPath + 'iPhoneEntitlement.plist'

#拼接原始ipa文件目录
sourceIPAName = sys.argv[1]
sourceIPA = os.path.join(scriptPath,sourceIPAName)

#拼接解压临时目录
targetTempDir = 'debug_' + os.path.basename(sourceIPA) + '.dir'
targetIPA = 'debug_' + os.path.basename(sys.argv[1])


shellTargetTempDir = shellquote(targetTempDir)
shellTargetIPA = shellquote(targetIPA)
shellEntitlementXML = shellquote(entitlementXML)
shellSourceIPA = shellquote(sourceIPA)

codeSignIdentifier = sys.argv[2]

print 'source :' + sourceIPA
print 'temp :' + targetTempDir

useOldData=0

if useOldData == 0:
	os.system('rm -rf {}'.format(shellTargetTempDir))

os.system('rm -rf {}'.format(shellTargetIPA))
# os.system('rm -rf {}'.format(shellEntitlementXML))



#获取开发者ID
mobileprovisionText = commands.getoutput('security cms -D -i ./embedded.mobileprovision')
fakeFile = StringIO.StringIO(mobileprovisionText)
mobileprovisionDic = plistlib.readPlist(fakeFile)
developerID = mobileprovisionDic['ApplicationIdentifierPrefix']
 
if developerID == None or len(developerID) != 1 :
	print 'get developerID from embedded.mobileprovision fail'
	exit()

developerID = developerID[0]

print developerID



#解压 ipa
os.system('mkdir {}'.format(shellTargetTempDir))

if useOldData == 0:
	os.system('cd {} && tar -zxf {}'.format(shellTargetTempDir, shellSourceIPA))
else:
	os.system('cd {} '.format(shellTargetTempDir))


#删除不需要的文件
os.system("find . -name SC_Info -exec rm -rf {} \;")
os.system("find . -name iTunesMetadata.plist -exec rm -rf {} \;")



# shellExePath = shellquote(exePath)
findAppPathCommand = 'find ./{} -depth 2 -name *.app'.format(shellTargetTempDir);
print findAppPathCommand
appPath = commands.getoutput(findAppPathCommand)


print 'appPath :' + appPath

#暂不处理插件，删除
os.system('rm -rf "{}"/PlugIns'.format(appPath));

#获取bundleID
infoPlistPath = commands.getoutput('find "{}" -depth 1 -iname info.plist'.format(appPath))
commands.getoutput('plutil -convert xml1 "{}" '.format(infoPlistPath))
info = plistlib.readPlist(infoPlistPath)
bundleID = info['CFBundleIdentifier']
commands.getoutput('plutil -convert binary1 "{}" '.format(infoPlistPath))

if bundleID == '':
	print 'can not find bundleID'
	exit()



fileHandle = open(entitlementXML, 'r+')
xmlText = fileHandle.read()
#对于已有字段,将其废掉
xmlText = xmlText.replace("com.example",bundleID)
xmlText = xmlText.replace("abcDevID",developerID)
fileHandle.close()

fileHandle = open(entitlementPlist, 'w')
fileHandle.write(xmlText)
fileHandle.close()


cpCommand = 'cp ./embedded.mobileprovision "{}"/'.format(appPath)
print 'cp mobileprovision :' + cpCommand
os.system(cpCommand)


signCommand = '/usr/bin/codesign --verbose=4 --force --no-strict --all-architectures -s "{}" --entitlements "{}" "{}"'.format(codeSignIdentifier, entitlementPlist, appPath)
print 'codesign :' + signCommand
os.system(signCommand)



#完成操作,重新打包
os.system('cd ' + shellTargetTempDir \
          + '&&' + 'zip --symlinks -r -q -9 ' + shellTargetIPA +' *' \
          + '&& mv ' + shellTargetIPA  + ' ../')



#os.system('rm -rf {}'.format(shellTargetTempDir))


