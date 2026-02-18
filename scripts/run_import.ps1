$history = "C:\Users\admin\Downloads\ExportHistory_01.02.25_17.02.26.csv"
$keva = "C:\Users\admin\Downloads\ExportKeva_NedarimPlus (3).csv"
python scripts/import_nedarim_csv.py --history $history --keva $keva --create-missing
