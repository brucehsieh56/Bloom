# -*- mode: python -*-

block_cipher = None


a = Analysis(['window.py'],
             pathex=['/Users/thsieh4/Google Drive/Bloomify/tracked_code/Bloom/Venus Flytrap'],
             binaries=[],
             datas=[('mortality_table.csv.gz', '.'),
                    ('year_of_birth_counts.csv.gz', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='window',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False )
app = BUNDLE(exe,
             name='window.app',
             icon=None,
             bundle_identifier=None)
