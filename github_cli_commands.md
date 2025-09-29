# STM32 Team GitHub CLI Commands

## View the issue:
```bash
gh issue view 3
```

## Comment on issue:
```bash
gh issue comment 3 --body "Working on STM32 firmware implementation"
```

## Close issue when fixed:
```bash  
gh issue close 3 --comment "Fixed: CV:DATA? and DPV:DATA? now return proper voltage,current format"
```

## Create labels for better organization:
```bash
gh label create "firmware" --description "STM32 firmware related issues" --color "ff6b6b"
gh label create "scpi" --description "SCPI protocol implementation" --color "4ecdc4"
```