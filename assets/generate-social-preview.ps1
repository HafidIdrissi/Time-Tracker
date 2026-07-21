param(
    [string]$OutputPath = (Join-Path $PSScriptRoot "social-preview.png")
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

function New-RoundedRectanglePath {
    param(
        [float]$X,
        [float]$Y,
        [float]$Width,
        [float]$Height,
        [float]$Radius
    )

    $path = [System.Drawing.Drawing2D.GraphicsPath]::new()
    $diameter = $Radius * 2
    $path.AddArc($X, $Y, $diameter, $diameter, 180, 90)
    $path.AddArc($X + $Width - $diameter, $Y, $diameter, $diameter, 270, 90)
    $path.AddArc($X + $Width - $diameter, $Y + $Height - $diameter, $diameter, $diameter, 0, 90)
    $path.AddArc($X, $Y + $Height - $diameter, $diameter, $diameter, 90, 90)
    $path.CloseFigure()
    return $path
}

function Fill-RoundedRectangle {
    param(
        [System.Drawing.Graphics]$Graphics,
        [System.Drawing.Brush]$Brush,
        [float]$X,
        [float]$Y,
        [float]$Width,
        [float]$Height,
        [float]$Radius
    )

    $path = New-RoundedRectanglePath -X $X -Y $Y -Width $Width -Height $Height -Radius $Radius
    try {
        $Graphics.FillPath($Brush, $path)
    }
    finally {
        $path.Dispose()
    }
}

function Draw-RoundedRectangle {
    param(
        [System.Drawing.Graphics]$Graphics,
        [System.Drawing.Pen]$Pen,
        [float]$X,
        [float]$Y,
        [float]$Width,
        [float]$Height,
        [float]$Radius
    )

    $path = New-RoundedRectanglePath -X $X -Y $Y -Width $Width -Height $Height -Radius $Radius
    try {
        $Graphics.DrawPath($Pen, $path)
    }
    finally {
        $path.Dispose()
    }
}

$width = 1280
$height = 640
$bitmap = [System.Drawing.Bitmap]::new($width, $height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$resources = [System.Collections.Generic.List[System.IDisposable]]::new()

try {
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit

    $backgroundRectangle = [System.Drawing.Rectangle]::new(0, 0, $width, $height)
    $background = [System.Drawing.Drawing2D.LinearGradientBrush]::new(
        $backgroundRectangle,
        [System.Drawing.ColorTranslator]::FromHtml("#111827"),
        [System.Drawing.ColorTranslator]::FromHtml("#312e81"),
        18
    )
    $resources.Add($background)
    $graphics.FillRectangle($background, $backgroundRectangle)

    $gridPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(20, 255, 255, 255), 1)
    $resources.Add($gridPen)
    for ($x = 0; $x -le $width; $x += 64) {
        $graphics.DrawLine($gridPen, $x, 0, $x, $height)
    }
    for ($y = 0; $y -le $height; $y += 64) {
        $graphics.DrawLine($gridPen, 0, $y, $width, $y)
    }

    $whiteBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::White)
    $mutedBrush = [System.Drawing.SolidBrush]::new([System.Drawing.ColorTranslator]::FromHtml("#cbd5e1"))
    $accentBrush = [System.Drawing.SolidBrush]::new([System.Drawing.ColorTranslator]::FromHtml("#a5b4fc"))
    $purpleBrush = [System.Drawing.SolidBrush]::new([System.Drawing.ColorTranslator]::FromHtml("#4f46e5"))
    $cyanBrush = [System.Drawing.SolidBrush]::new([System.Drawing.ColorTranslator]::FromHtml("#0ea5e9"))
    $amberBrush = [System.Drawing.SolidBrush]::new([System.Drawing.ColorTranslator]::FromHtml("#f59e0b"))
    $cardBrush = [System.Drawing.SolidBrush]::new([System.Drawing.ColorTranslator]::FromHtml("#f8fafc"))
    $innerCardBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::White)
    $inkBrush = [System.Drawing.SolidBrush]::new([System.Drawing.ColorTranslator]::FromHtml("#172033"))
    $secondaryInkBrush = [System.Drawing.SolidBrush]::new([System.Drawing.ColorTranslator]::FromHtml("#64748b"))
    $pillBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(30, 255, 255, 255))

    @($whiteBrush, $mutedBrush, $accentBrush, $purpleBrush, $cyanBrush, $amberBrush,
      $cardBrush, $innerCardBrush, $inkBrush, $secondaryInkBrush, $pillBrush) |
        ForEach-Object { $resources.Add($_) }

    $brandFont = [System.Drawing.Font]::new("Segoe UI", 17, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
    $headlineFont = [System.Drawing.Font]::new("Segoe UI", 49, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
    $bodyFont = [System.Drawing.Font]::new("Segoe UI", 23, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
    $pillFont = [System.Drawing.Font]::new("Segoe UI", 13, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
    $urlFont = [System.Drawing.Font]::new("Segoe UI", 16, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
    $dashboardTitleFont = [System.Drawing.Font]::new("Segoe UI", 18, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
    $metricFont = [System.Drawing.Font]::new("Segoe UI", 30, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
    $smallFont = [System.Drawing.Font]::new("Segoe UI", 13, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
    $smallBoldFont = [System.Drawing.Font]::new("Segoe UI", 13, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)

    @($brandFont, $headlineFont, $bodyFont, $pillFont, $urlFont, $dashboardTitleFont,
      $metricFont, $smallFont, $smallBoldFont) | ForEach-Object { $resources.Add($_) }

    $graphics.DrawString("LOCAL TIME TRACKER", $brandFont, $accentBrush, 66, 68)
    $graphics.DrawString(
        "See where your`nWindows time goes.",
        $headlineFont,
        $whiteBrush,
        [System.Drawing.RectangleF]::new(62, 126, 570, 150)
    )
    $graphics.DrawString(
        "Private by design. No account,`nno cloud, no telemetry.",
        $bodyFont,
        $mutedBrush,
        [System.Drawing.RectangleF]::new(66, 310, 535, 76)
    )

    $pillY = 424
    $pillDefinitions = @(
        @{ X = 66; Width = 148; Text = "WINDOWS 10 & 11" },
        @{ X = 226; Width = 122; Text = "OPEN SOURCE" },
        @{ X = 360; Width = 124; Text = "LOCAL SQLITE" }
    )
    foreach ($pill in $pillDefinitions) {
        Fill-RoundedRectangle -Graphics $graphics -Brush $pillBrush -X $pill.X -Y $pillY -Width $pill.Width -Height 36 -Radius 18
        $format = [System.Drawing.StringFormat]::new()
        $format.Alignment = [System.Drawing.StringAlignment]::Center
        $format.LineAlignment = [System.Drawing.StringAlignment]::Center
        $graphics.DrawString(
            $pill.Text,
            $pillFont,
            $whiteBrush,
            [System.Drawing.RectangleF]::new($pill.X, $pillY, $pill.Width, 36),
            $format
        )
        $format.Dispose()
    }

    $graphics.DrawString(
        "github.com/HafidIdrissi/Time-Tracker",
        $urlFont,
        $mutedBrush,
        66,
        551
    )

    $shadowBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(45, 0, 0, 0))
    $resources.Add($shadowBrush)
    Fill-RoundedRectangle -Graphics $graphics -Brush $shadowBrush -X 681 -Y 58 -Width 535 -Height 530 -Radius 24
    Fill-RoundedRectangle -Graphics $graphics -Brush $cardBrush -X 670 -Y 46 -Width 535 -Height 530 -Radius 24

    $graphics.DrawString("TODAY", $dashboardTitleFont, $inkBrush, 702, 78)
    $statusFormat = [System.Drawing.StringFormat]::new()
    $statusFormat.Alignment = [System.Drawing.StringAlignment]::Far
    $graphics.DrawString(
        "LOCAL ONLY",
        $smallBoldFont,
        $purpleBrush,
        [System.Drawing.RectangleF]::new(1010, 81, 155, 24),
        $statusFormat
    )
    $statusFormat.Dispose()

    Fill-RoundedRectangle -Graphics $graphics -Brush $innerCardBrush -X 700 -Y 125 -Width 225 -Height 112 -Radius 14
    Fill-RoundedRectangle -Graphics $graphics -Brush $innerCardBrush -X 943 -Y 125 -Width 232 -Height 112 -Radius 14
    $graphics.DrawString("ACTIVE TIME", $smallBoldFont, $secondaryInkBrush, 722, 147)
    $graphics.DrawString("6 h 24 min", $metricFont, $inkBrush, 720, 176)
    $graphics.DrawString("IDLE DETECTED", $smallBoldFont, $secondaryInkBrush, 965, 147)
    $graphics.DrawString("1 h 08 min", $metricFont, $inkBrush, 963, 176)

    Fill-RoundedRectangle -Graphics $graphics -Brush $innerCardBrush -X 700 -Y 255 -Width 475 -Height 142 -Radius 14
    $graphics.DrawString("USAGE BY HOUR", $smallBoldFont, $inkBrush, 722, 276)
    $chartPen = [System.Drawing.Pen]::new([System.Drawing.ColorTranslator]::FromHtml("#e2e8f0"), 1)
    $resources.Add($chartPen)
    for ($line = 0; $line -lt 4; $line++) {
        $lineY = 307 + ($line * 22)
        $graphics.DrawLine($chartPen, 723, $lineY, 1147, $lineY)
    }
    $barValues = @(28, 42, 55, 35, 68, 80, 61, 88, 64, 46, 29, 52)
    for ($index = 0; $index -lt $barValues.Count; $index++) {
        $barX = 731 + ($index * 34)
        $barHeight = [float]$barValues[$index]
        $barBrush = if ($index -in @(5, 7)) { $cyanBrush } else { $purpleBrush }
        Fill-RoundedRectangle -Graphics $graphics -Brush $barBrush -X $barX -Y (378 - $barHeight) -Width 19 -Height $barHeight -Radius 5
    }

    Fill-RoundedRectangle -Graphics $graphics -Brush $innerCardBrush -X 700 -Y 415 -Width 475 -Height 126 -Radius 14
    $graphics.DrawString("TOP APPLICATIONS", $smallBoldFont, $inkBrush, 722, 437)
    $applicationRows = @(
        @{ Name = "Code.exe"; Duration = "3 h 12 min"; Color = $purpleBrush },
        @{ Name = "chrome.exe"; Duration = "1 h 38 min"; Color = $cyanBrush },
        @{ Name = "Explorer.exe"; Duration = "42 min"; Color = $amberBrush }
    )
    $rowY = 468
    foreach ($row in $applicationRows) {
        $graphics.FillEllipse($row.Color, 724, $rowY + 4, 9, 9)
        $graphics.DrawString($row.Name, $smallFont, $inkBrush, 744, $rowY)
        $durationFormat = [System.Drawing.StringFormat]::new()
        $durationFormat.Alignment = [System.Drawing.StringAlignment]::Far
        $graphics.DrawString(
            $row.Duration,
            $smallBoldFont,
            $inkBrush,
            [System.Drawing.RectangleF]::new(1010, $rowY, 136, 20),
            $durationFormat
        )
        $durationFormat.Dispose()
        $rowY += 24
    }

    $outputDirectory = Split-Path -Parent $OutputPath
    if ($outputDirectory -and -not (Test-Path -LiteralPath $outputDirectory)) {
        New-Item -ItemType Directory -Path $outputDirectory | Out-Null
    }
    $bitmap.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
    Write-Output (Resolve-Path -LiteralPath $OutputPath)
}
finally {
    foreach ($resource in $resources) {
        $resource.Dispose()
    }
    $graphics.Dispose()
    $bitmap.Dispose()
}
