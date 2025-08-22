using System.IO;
using System.Text.Json;

public class Settings
{
    private static readonly string settingsFilePath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "settings.json");

    public string LastUsedDirectory { get; set; }

    public static Settings Load()
    {
        if (File.Exists(settingsFilePath))
        {
            var json = File.ReadAllText(settingsFilePath);
            return JsonSerializer.Deserialize<Settings>(json);
        }
        return new Settings();
    }

    public void Save()
    {
        var json = JsonSerializer.Serialize(this);
        File.WriteAllText(settingsFilePath, json);
    }
}
