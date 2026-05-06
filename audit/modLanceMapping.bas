Option Explicit
Option Private Module

' ================================================================
' modLanceMapping
' ================================================================


Public Function ResolveArmpilLanceMap(ByVal levelsCsv As String, Optional ByVal allLevelsCsv As String = "") As String
    Dim defaultLances As String
    Dim defaultMap As String
    Dim defaultPairs As String
    Dim identifiedLevelsCsv As String
    Dim manualLevelsCsv As String
    Dim levelCount As Long
    Dim choice As VbMsgBoxResult
    Dim prompt As String
    Dim resp As String
    Dim mapText As String
    Dim manualDefault As String
    Dim manualMap As String
    Dim defaultDisplay As String
    Dim suggestionLabel As String
    Dim knownLancesCsv As String

    levelCount = CountCsvItems(levelsCsv)
    If levelCount <= 0 Then Exit Function

    identifiedLevelsCsv = Trim$(levelsCsv)
    manualLevelsCsv = Trim$(allLevelsCsv)
    If manualLevelsCsv = "" Then manualLevelsCsv = identifiedLevelsCsv

    knownLancesCsv = GetKnownLancesForPython()
    defaultLances = GetSuggestedArmpilLances(identifiedLevelsCsv, knownLancesCsv)
    defaultMap = BuildLanceMapFromLists(identifiedLevelsCsv, defaultLances)
    defaultPairs = BuildLanceLevelListFromMap(defaultMap)
    If knownLancesCsv <> "" Then
        suggestionLabel = "Mapa sugerido pelos lances ja carregados no SELE:"
    Else
        suggestionLabel = "Mapa sugerido pelo padrao local (SELE ainda nao carregado):"
    End If
    defaultDisplay = defaultPairs
    If Trim$(defaultDisplay) = "" Then
        defaultDisplay = "(nenhuma sugestao automatica encontrada)"
    End If

    If defaultMap <> "" Then
        choice = MsgBox( _
            "Niveis uteis identificados pelo script:" & vbCrLf & _
            "  " & FormatLevelsForPrompt(identifiedLevelsCsv) & vbCrLf & vbCrLf & _
            suggestionLabel & vbCrLf & _
            "  " & defaultDisplay & vbCrLf & vbCrLf & _
            "Sim = usar sugestao" & vbCrLf & _
            "Nao = mapear manualmente com todos os niveis detectados" & vbCrLf & _
            "Cancelar = cancelar", _
            vbQuestion + vbYesNoCancel, _
            "Mapear lances ARMPIL" _
        )

        If choice = vbYes Then
            ResolveArmpilLanceMap = defaultMap
            Exit Function
        End If

        If choice = vbCancel Then Exit Function
    Else
        choice = MsgBox( _
            "Niveis uteis identificados pelo script:" & vbCrLf & _
            "  " & FormatLevelsForPrompt(identifiedLevelsCsv) & vbCrLf & vbCrLf & _
            suggestionLabel & vbCrLf & _
            "  " & defaultDisplay & vbCrLf & vbCrLf & _
            "OK = mapear manualmente com todos os niveis detectados" & vbCrLf & _
            "Cancelar = cancelar", _
            vbInformation + vbOKCancel, _
            "Mapear lances ARMPIL" _
        )

        If choice <> vbOK Then Exit Function
    End If

    manualMap = defaultMap
    If Trim$(manualMap) = "" Then manualMap = BuildLanceMapFromLists(manualLevelsCsv, GetSuggestedArmpilLances(manualLevelsCsv, knownLancesCsv))
    manualDefault = BuildLanceLevelDefaultForLevels(manualLevelsCsv, manualMap)

    prompt = BuildArmpilManualPrompt(manualLevelsCsv, identifiedLevelsCsv, defaultPairs)

    Do
        resp = InputBox(prompt, "Mapear lances ARMPIL", manualDefault)
        If Trim$(resp) = "" Then Exit Function

        mapText = BuildLanceMapFromLists(manualLevelsCsv, resp)
        If mapText <> "" Then
            ResolveArmpilLanceMap = mapText
            Exit Function
        End If

        MsgBox BuildArmpilMapErrorMessage(defaultPairs), vbExclamation, "Mapear lances ARMPIL"
    Loop
End Function

Public Function BuildExplicitLanceMap(ByVal rawText As String) As String
    Dim normalized As String
    Dim parts() As String
    Dim i As Long
    Dim chunk As String
    Dim sepPos As Long
    Dim isLanceLevelPair As Boolean
    Dim levelText As String
    Dim lanceText As String

    normalized = Trim$(rawText)
    normalized = Replace(normalized, "->", "=")
    normalized = Replace(normalized, "=>", "=")
    normalized = Replace(normalized, vbCrLf, ";")
    normalized = Replace(normalized, vbCr, ";")
    normalized = Replace(normalized, vbLf, ";")
    normalized = Replace(normalized, " e ", ";")

    parts = Split(normalized, ";")

    For i = LBound(parts) To UBound(parts)
        chunk = Trim$(parts(i))
        If chunk = "" Then GoTo NextPair

        sepPos = InStr(1, chunk, "=", vbTextCompare)
        isLanceLevelPair = False
        If InStr(1, chunk, ":", vbTextCompare) > 0 Then
            sepPos = InStr(1, chunk, ":", vbTextCompare)
            isLanceLevelPair = True
        End If

        If sepPos <= 1 Or sepPos >= Len(chunk) Then Exit Function

        If isLanceLevelPair Then
            lanceText = Trim$(Left$(chunk, sepPos - 1))
            levelText = Trim$(Mid$(chunk, sepPos + 1))
        Else
            levelText = Trim$(Left$(chunk, sepPos - 1))
            lanceText = Trim$(Mid$(chunk, sepPos + 1))

            If LooksLikeLanceLevelPair(levelText, lanceText) Then
                Dim tmpText As String
                tmpText = levelText
                levelText = lanceText
                lanceText = tmpText
            End If
        End If

        If Left$(levelText, 1) = "+" Then levelText = Mid$(levelText, 2)
        levelText = Replace(levelText, ",", ".")

        If levelText = "" Then Exit Function
        If Not IsNumeric(lanceText) Then Exit Function
        If CLng(Val(lanceText)) = 0 Then GoTo NextPair

        If BuildExplicitLanceMap <> "" Then BuildExplicitLanceMap = BuildExplicitLanceMap & ";"
        BuildExplicitLanceMap = BuildExplicitLanceMap & levelText & "=" & CLng(lanceText)
NextPair:
    Next i
End Function

Public Function LooksLikeLanceLevelPair(ByVal leftText As String, ByVal rightText As String) As Boolean
    Dim leftValue As Double
    Dim rightValue As Double

    leftText = Replace(Replace(Trim$(leftText), "+", ""), ",", ".")
    rightText = Replace(Replace(Trim$(rightText), "+", ""), ",", ".")

    leftValue = Val(leftText)
    rightValue = Val(rightText)
    If leftValue <= 0# Or rightValue <= 0# Then Exit Function

    LooksLikeLanceLevelPair = (leftValue < 200# And rightValue >= 200#)
End Function

Public Function IsExplicitLanceMapText(ByVal rawText As String) As Boolean
    IsExplicitLanceMapText = _
        InStr(1, rawText, "=", vbTextCompare) > 0 Or _
        InStr(1, rawText, ":", vbTextCompare) > 0 Or _
        InStr(1, rawText, "->", vbTextCompare) > 0
End Function

Public Function BuildLanceLevelListFromMap(ByVal mapText As String) As String
    Dim parts() As String
    Dim i As Long
    Dim chunk As String
    Dim sepPos As Long
    Dim levelText As String
    Dim lanceText As String

    If Trim$(mapText) = "" Then Exit Function

    parts = Split(mapText, ";")
    For i = LBound(parts) To UBound(parts)
        chunk = Trim$(parts(i))
        If chunk = "" Then GoTo NextItem

        sepPos = InStr(1, chunk, "=", vbTextCompare)
        If sepPos <= 1 Or sepPos >= Len(chunk) Then GoTo NextItem

        levelText = Trim$(Left$(chunk, sepPos - 1))
        lanceText = Trim$(Mid$(chunk, sepPos + 1))
        If Left$(levelText, 1) <> "+" Then levelText = "+" & levelText

        If BuildLanceLevelListFromMap <> "" Then BuildLanceLevelListFromMap = BuildLanceLevelListFromMap & "; "
        BuildLanceLevelListFromMap = BuildLanceLevelListFromMap & lanceText & ":" & levelText
NextItem:
    Next i
End Function

Public Function BuildLanceMapFromLists(ByVal levelsCsv As String, ByVal lancesCsv As String) As String
    Dim levelParts() As String
    Dim lanceParts() As String
    Dim i As Long
    Dim levelCount As Long
    Dim lanceCount As Long
    Dim token As String
    Dim rawText As String

    rawText = Trim$(lancesCsv)
    If IsExplicitLanceMapText(rawText) Then
        BuildLanceMapFromLists = BuildExplicitLanceMap(rawText)
        Exit Function
    End If

    lancesCsv = Replace(lancesCsv, ";", ",")
    lancesCsv = Replace(lancesCsv, vbCrLf, ",")
    lancesCsv = Replace(lancesCsv, vbCr, ",")
    lancesCsv = Replace(lancesCsv, vbLf, ",")

    If Trim$(levelsCsv) = "" Or Trim$(lancesCsv) = "" Then Exit Function

    levelParts = Split(levelsCsv, ",")
    lanceParts = Split(lancesCsv, ",")
    levelCount = UBound(levelParts) - LBound(levelParts) + 1
    lanceCount = UBound(lanceParts) - LBound(lanceParts) + 1

    Do While lanceCount > 0
        If Trim$(lanceParts(lanceCount - 1)) <> "" Then Exit Do
        lanceCount = lanceCount - 1
    Loop

    If lanceCount > levelCount Then Exit Function

    For i = 0 To lanceCount - 1
        token = Trim$(lanceParts(i))
        If token = "" Then GoTo NextItem
        If Not IsNumeric(token) Then Exit Function
        If CLng(Val(token)) = 0 Then GoTo NextItem

        If BuildLanceMapFromLists <> "" Then BuildLanceMapFromLists = BuildLanceMapFromLists & ";"
        BuildLanceMapFromLists = BuildLanceMapFromLists & Trim$(levelParts(i)) & "=" & CLng(token)
NextItem:
    Next i
End Function

Public Function GetSuggestedArmpilLances(ByVal levelsCsv As String, Optional ByVal knownLancesCsv As String = "") As String
    Dim raw As String
    Dim parts() As String
    Dim startIndex As Long
    Dim partCount As Long
    Dim blankCount As Long
    Dim pos As Long
    Dim i As Long
    Dim levelCount As Long

    levelCount = CountCsvItems(levelsCsv)
    If levelCount <= 0 Then Exit Function

    raw = Trim$(knownLancesCsv)
    If raw = "" Then raw = GetKnownLancesForPython()
    If raw = "" Then
        GetSuggestedArmpilLances = BuildFallbackArmpilLancesFromLevels(levelsCsv)
        Exit Function
    End If

    parts = Split(raw, ",")
    partCount = UBound(parts) - LBound(parts) + 1

    If partCount > levelCount Then
        startIndex = UBound(parts) - levelCount + 1
        partCount = levelCount
        blankCount = 0
    Else
        startIndex = LBound(parts)
        blankCount = levelCount - partCount
    End If

    For pos = 1 To levelCount
        If pos > 1 Then GetSuggestedArmpilLances = GetSuggestedArmpilLances & ","
        If pos > blankCount Then
            i = startIndex + pos - blankCount - 1
            GetSuggestedArmpilLances = GetSuggestedArmpilLances & Trim$(parts(i))
        End If
    Next pos
End Function

Public Function BuildFallbackArmpilLancesFromLevels(ByVal levelsCsv As String) As String
    Dim levelParts() As String
    Dim lanceValues() As Long
    Dim hasValue() As Boolean
    Dim levelCount As Long
    Dim i As Long
    Dim anchorIndex As Long
    Dim currentLance As Long
    Dim defaultLance As Long

    If Trim$(levelsCsv) = "" Then Exit Function

    levelParts = Split(levelsCsv, ",")
    levelCount = UBound(levelParts) - LBound(levelParts) + 1
    If levelCount <= 0 Then Exit Function

    ReDim lanceValues(0 To levelCount - 1)
    ReDim hasValue(0 To levelCount - 1)

    anchorIndex = -1
    For i = 0 To levelCount - 1
        If TryGetDefaultArmpilLanceForLevel(levelParts(i), defaultLance) Then
            lanceValues(i) = defaultLance
            hasValue(i) = True
            If anchorIndex = -1 And defaultLance > 0 Then anchorIndex = i
        End If
    Next i

    If anchorIndex = -1 Then Exit Function

    currentLance = lanceValues(anchorIndex)
    For i = anchorIndex - 1 To 0 Step -1
        If hasValue(i) Then
            If lanceValues(i) > 0 Then currentLance = lanceValues(i)
        Else
            currentLance = currentLance - 1
            If currentLance > 0 Then
                lanceValues(i) = currentLance
                hasValue(i) = True
            End If
        End If
    Next i

    currentLance = lanceValues(anchorIndex)
    For i = anchorIndex + 1 To levelCount - 1
        If hasValue(i) Then
            If lanceValues(i) > 0 Then currentLance = lanceValues(i)
        Else
            currentLance = currentLance + 1
            lanceValues(i) = currentLance
            hasValue(i) = True
        End If
    Next i

    For i = 0 To levelCount - 1
        If i > 0 Then BuildFallbackArmpilLancesFromLevels = BuildFallbackArmpilLancesFromLevels & ","
        If hasValue(i) Then BuildFallbackArmpilLancesFromLevels = BuildFallbackArmpilLancesFromLevels & CStr(lanceValues(i))
    Next i
End Function

Public Function TryGetDefaultArmpilLanceForLevel(ByVal levelText As String, ByRef lanceValue As Long) As Boolean
    Dim normalizedLevel As String
    Dim levelValue As Double

    normalizedLevel = NormalizeLevelToken(levelText)
    levelValue = Val(normalizedLevel)
    If levelValue <= 0# Then Exit Function

    If Abs(levelValue - 1040.25) < 0.01 Then
        lanceValue = 0
        TryGetDefaultArmpilLanceForLevel = True
    ElseIf Abs(levelValue - 1043.4) < 0.01 Then
        lanceValue = 6
        TryGetDefaultArmpilLanceForLevel = True
    ElseIf Abs(levelValue - 1046.6) < 0.01 Then
        lanceValue = 7
        TryGetDefaultArmpilLanceForLevel = True
    End If
End Function

Public Function FormatLevelsForPrompt(ByVal levelsCsv As String) As String
    Dim parts() As String
    Dim i As Long

    If Trim$(levelsCsv) = "" Then Exit Function

    parts = Split(levelsCsv, ",")
    For i = 0 To UBound(parts)
        If FormatLevelsForPrompt <> "" Then FormatLevelsForPrompt = FormatLevelsForPrompt & ", "
        FormatLevelsForPrompt = FormatLevelsForPrompt & "+" & Trim$(parts(i))
    Next i
End Function

Public Function BuildArmpilLevelsPrompt(ByVal allLevelsCsv As String, ByVal mappedLevelsCsv As String) As String
    BuildArmpilLevelsPrompt = "Todos os niveis detectados no PDF:" & vbCrLf & _
        "  " & FormatLevelsForPrompt(allLevelsCsv)

    If Trim$(mappedLevelsCsv) <> "" And Trim$(allLevelsCsv) <> Trim$(mappedLevelsCsv) Then
        BuildArmpilLevelsPrompt = BuildArmpilLevelsPrompt & vbCrLf & vbCrLf & _
            "Niveis com armadura para mapear:" & vbCrLf & _
            "  " & FormatLevelsForPrompt(mappedLevelsCsv)
    End If
End Function

Public Function BuildArmpilManualPrompt(ByVal allLevelsCsv As String, ByVal identifiedLevelsCsv As String, ByVal defaultPairs As String) As String
    If Trim$(identifiedLevelsCsv) <> "" And Trim$(identifiedLevelsCsv) <> Trim$(allLevelsCsv) Then
        BuildArmpilManualPrompt = _
            "Todos os niveis detectados no PDF (inclui niveis ignorados pelo script):" & vbCrLf & _
            "  " & FormatLevelsForPrompt(allLevelsCsv) & vbCrLf & vbCrLf
    Else
        BuildArmpilManualPrompt = _
            "Niveis detectados no PDF:" & vbCrLf & _
            "  " & FormatLevelsForPrompt(allLevelsCsv) & vbCrLf & vbCrLf
    End If

    BuildArmpilManualPrompt = BuildArmpilManualPrompt & _
        "Edite os pares lance:nivel sugeridos abaixo." & vbCrLf & _
        "Use lance 0 para ignorar um nivel sem armadura util." & vbCrLf & _
        "Ex.: " & IIf(Trim$(defaultPairs) <> "", defaultPairs, "6:+1043.40; 7:+1046.60")
End Function

Public Function BuildArmpilMapErrorMessage(ByVal defaultPairs As String) As String
    BuildArmpilMapErrorMessage = _
        "Entrada invalida." & vbCrLf & vbCrLf & _
        "Use uma destas opcoes:" & vbCrLf & _
        "1. Pares no formato lance:nivel." & vbCrLf & _
        "   Use lance 0 para ignorar. Ex.: " & IIf(Trim$(defaultPairs) <> "", defaultPairs, "0:+1040.25; 6:+1043.40; 7:+1046.60") & vbCrLf & vbCrLf & _
        "2. Somente os lances na ordem dos niveis, separados por virgula." & vbCrLf & _
        "   Ex.: 0,6,7,8"
End Function

Public Function BuildLanceLevelDefaultForLevels(ByVal levelsCsv As String, ByVal mapText As String) As String
    Dim dict As Object
    Set dict = CreateObject("Scripting.Dictionary")

    Dim parts() As String
    Dim i As Long
    Dim chunk As String
    Dim sepPos As Long
    Dim levelText As String
    Dim lanceText As String
    Dim levelParts() As String
    Dim normalizedLevel As String
    Dim displayLevel As String

    If Trim$(levelsCsv) = "" Then Exit Function

    If Trim$(mapText) <> "" Then
        parts = Split(mapText, ";")
        For i = LBound(parts) To UBound(parts)
            chunk = Trim$(parts(i))
            If chunk = "" Then GoTo NextMapItem

            sepPos = InStr(1, chunk, "=", vbTextCompare)
            If sepPos <= 1 Or sepPos >= Len(chunk) Then GoTo NextMapItem

            levelText = Trim$(Left$(chunk, sepPos - 1))
            lanceText = Trim$(Mid$(chunk, sepPos + 1))
            normalizedLevel = NormalizeLevelToken(levelText)
            If normalizedLevel <> "" And lanceText <> "" Then dict(normalizedLevel) = lanceText
NextMapItem:
        Next i
    End If

    levelParts = Split(levelsCsv, ",")
    For i = LBound(levelParts) To UBound(levelParts)
        normalizedLevel = NormalizeLevelToken(levelParts(i))
        If normalizedLevel = "" Then GoTo NextLevel

        displayLevel = normalizedLevel
        If Left$(displayLevel, 1) <> "+" Then displayLevel = "+" & displayLevel
        If BuildLanceLevelDefaultForLevels <> "" Then BuildLanceLevelDefaultForLevels = BuildLanceLevelDefaultForLevels & "; "

        If dict.Exists(normalizedLevel) Then
            BuildLanceLevelDefaultForLevels = BuildLanceLevelDefaultForLevels & CStr(dict(normalizedLevel)) & ":" & displayLevel
        Else
            BuildLanceLevelDefaultForLevels = BuildLanceLevelDefaultForLevels & "0:" & displayLevel
        End If
NextLevel:
    Next i
End Function

Public Function BuildLanceEntriesForLevels(ByVal levelsCsv As String, ByVal mapText As String) As String
    Dim dict As Object
    Set dict = CreateObject("Scripting.Dictionary")

    Dim parts() As String
    Dim i As Long
    Dim chunk As String
    Dim sepPos As Long
    Dim levelText As String
    Dim lanceText As String
    Dim levelParts() As String
    Dim normalizedLevel As String

    If Trim$(levelsCsv) = "" Or Trim$(mapText) = "" Then Exit Function

    parts = Split(mapText, ";")
    For i = LBound(parts) To UBound(parts)
        chunk = Trim$(parts(i))
        If chunk = "" Then GoTo NextMapItem

        sepPos = InStr(1, chunk, "=", vbTextCompare)
        If sepPos <= 1 Or sepPos >= Len(chunk) Then GoTo NextMapItem

        levelText = Trim$(Left$(chunk, sepPos - 1))
        lanceText = Trim$(Mid$(chunk, sepPos + 1))
        normalizedLevel = NormalizeLevelToken(levelText)
        If normalizedLevel <> "" And lanceText <> "" Then dict(normalizedLevel) = lanceText
NextMapItem:
    Next i

    levelParts = Split(levelsCsv, ",")
    For i = LBound(levelParts) To UBound(levelParts)
        If i > LBound(levelParts) Then BuildLanceEntriesForLevels = BuildLanceEntriesForLevels & ","
        normalizedLevel = NormalizeLevelToken(levelParts(i))
        If dict.Exists(normalizedLevel) Then
            BuildLanceEntriesForLevels = BuildLanceEntriesForLevels & CStr(dict(normalizedLevel))
        End If
    Next i
End Function

Public Function NormalizeLevelToken(ByVal levelText As String) As String
    levelText = Trim$(levelText)
    If Left$(levelText, 1) = "+" Then levelText = Mid$(levelText, 2)
    levelText = Replace(levelText, ",", ".")
    NormalizeLevelToken = levelText
End Function

Public Function GetKnownLancesForPython() As String
    Dim dict As Object
    Set dict = GetSheetLancesDict(ThisWorkbook.Sheets("SELE"), 6, 3)
    If dict.count = 0 Then Exit Function

    Dim keys As Variant
    keys = dict.keys
    SortNumericVariantArray keys
    GetKnownLancesForPython = JoinVariantList(keys)
End Function
