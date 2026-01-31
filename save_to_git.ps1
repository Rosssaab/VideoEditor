# Save VideoEditor project to git.
# Run in PowerShell from the project folder: .\save_to_git.ps1

Set-Location $PSScriptRoot

git add `
  AllCode/FinalEdits.py `
  AllCode/FinalEdits_settings.json `
  AllCode/create_final_video.py `
  AllCode/fix_manim_video_metadata.py `
  AllCode/run_all.py `
  AllCode/README.md `
  AllCode/requirements.txt `
  AllCode/BBC-Bg.jpg `
  save_to_git.ps1

git status
git commit -m "AllCode video pipeline: narrator + Manim text + audio

- AllCode/: self-contained pipeline (NaratorMp4, SoundFile, FinishedMp4, Temp)
- FinalEdits.py: 3 zoom cycles + final 100%, narrator off last 1s
- create_final_video.py: frame-rate sync (bg 60fps vs output 30fps), debug every 0.5s
- run_all.py: Manim -qh --disable_caching, opens final video when done
- Text 100% at end, narrator hidden 4-5s, 5s total duration"

Write-Host "Done. Push with: git push"
