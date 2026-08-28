package com.assaneai.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

private val AssaneDarkScheme = darkColorScheme(
    primary = SenegalGreen,
    secondary = SenegalYellow,
    tertiary = SenegalRed,
    background = AssaneBackground,
    surface = AssaneSurface,
    onBackground = AssaneText,
    onSurface = AssaneText,
)

private val AssaneLightScheme = androidx.compose.material3.lightColorScheme(
    primary = SenegalGreen,
    secondary = SenegalYellow,
    tertiary = SenegalRed,
    background = androidx.compose.ui.graphics.Color(0xFFF4F6F8),
    surface = androidx.compose.ui.graphics.Color.White,
    onBackground = androidx.compose.ui.graphics.Color(0xFF18202A),
    onSurface = androidx.compose.ui.graphics.Color(0xFF18202A),
)

@Composable
fun AssaneAITheme(darkTheme: Boolean = true, content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = if (darkTheme) AssaneDarkScheme else AssaneLightScheme,
        typography = AssaneTypography,
        content = content,
    )
}
