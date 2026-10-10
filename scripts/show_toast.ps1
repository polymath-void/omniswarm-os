param(
    [string]$Title = "OmniSwarm",
    [string]$Message = "New message received",
    [switch]$PlaySound = $true
)

try {
    # Play system notification sound
    if ($PlaySound) {
        [System.Media.SystemSounds]::Asterisk.Play()
    }

    # Attempt Windows 10/11 Toast Notification via WinRT
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
    $textNodes = $template.GetElementsByTagName("text")
    $textNodes.Item(0).AppendChild($template.CreateTextNode($Title)) | Out-Null
    $textNodes.Item(1).AppendChild($template.CreateTextNode($Message)) | Out-Null

    $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("OmniSwarm")
    $notification = [Windows.UI.Notifications.ToastNotification]::new($template)
    $notifier.Show($notification)
} catch {
    # Fallback to system console beep
    [Console]::Beep(1000, 200)
}
