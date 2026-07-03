Option Explicit
Option Private Module

' ================================================================
' modLanceMapping
' ================================================================

Private Const LANCE_MAP_SHEET_NAME As String = "__ARMPIL_MAPEAMENTO__"
Private Const LANCE_MAP_FIRST_DATA_ROW As Long = 9
Private Const LANCE_MAP_QUICK_INPUT_CELL As String = "B3"
Private Const LANCE_MAP_START_CELL As String = "B4"
Private Const ARMPIL_LANCE_MAP_NAME As String = "_ARMPIL_LANCE_LEVEL_MAP"

Private mLanceMapEditorAction As String


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
    prompt = BuildArmpilManualPrompt(manualLevelsCsv, identifiedLevelsCsv, defaultPairs)

    On Error GoTo UserFormFallback
    mapText = PromptArmpilLanceMapUserForm(manualLevelsCsv, identifiedLevelsCsv, manualMap, defaultPairs)
    On Error GoTo 0
    If mapText <> "" Then
        ResolveArmpilLanceMap = mapText
    End If
    Exit Function

UserFormFallback:
    Err.Clear
    On Error GoTo ManualFallback
    mapText = PromptArmpilLanceMapSheet(manualLevelsCsv, identifiedLevelsCsv, manualMap, prompt, defaultPairs)
    On Error GoTo 0
    If mapText <> "" Then
        ResolveArmpilLanceMap = mapText
    End If
    Exit Function

ManualFallback:
    Err.Clear
    On Error GoTo 0

    Do
        resp = InputBox(prompt, "Mapear lances ARMPIL", BuildLanceLevelDefaultForLevels(manualLevelsCsv, manualMap))
        If Trim$(resp) = "" Then Exit Function

        mapText = BuildLanceMapFromLists(manualLevelsCsv, resp)
        If mapText <> "" Then
            ResolveArmpilLanceMap = mapText
            Exit Function
        End If

        MsgBox BuildArmpilMapErrorMessage(defaultPairs), vbExclamation, "Mapear lances ARMPIL"
    Loop
End Function

Public Function PromptArmpilLanceMapUserForm( _
    ByVal allLevelsCsv As String, _
    ByVal identifiedLevelsCsv As String, _
    ByVal defaultMap As String, _
    ByVal defaultPairs As String _
) As String
    Dim frm As Object

    Set frm = VBA.UserForms.Add("frmArmpilLanceMap")
    CallByName frm, "SetupEditor", VbMethod, allLevelsCsv, identifiedLevelsCsv, defaultMap, defaultPairs
    frm.Show vbModal
    PromptArmpilLanceMapUserForm = CStr(CallByName(frm, "ResultMapText", VbGet))

    On Error Resume Next
    Unload frm
    Set frm = Nothing
    On Error GoTo 0
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
    If TryBuildShiftedLanceMapFromStart(levelsCsv, rawText, BuildLanceMapFromLists) Then Exit Function

    If ContainsLanceRuleSyntax(rawText) Then
        BuildLanceMapFromLists = BuildLanceMapFromRules(levelsCsv, rawText)
        If BuildLanceMapFromLists <> "" Then Exit Function
    End If

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

Public Function PromptArmpilLanceMapSheet( _
    ByVal allLevelsCsv As String, _
    ByVal identifiedLevelsCsv As String, _
    ByVal defaultMap As String, _
    ByVal promptText As String, _
    ByVal defaultPairs As String _
) As String
    Dim ws As Worksheet
    Dim previousSheet As Worksheet

    On Error Resume Next
    Set previousSheet = ActiveSheet
    On Error GoTo 0

    Set ws = PrepareArmpilLanceMapSheet(allLevelsCsv, identifiedLevelsCsv, defaultMap, promptText)
    ws.Activate

    Do
        mLanceMapEditorAction = ""
        WaitForLanceMapEditorAction ws.Name

        If mLanceMapEditorAction = "cancel" Then Exit Do

        PromptArmpilLanceMapSheet = ReadLanceMapFromEditorSheet(ws, allLevelsCsv)
        If PromptArmpilLanceMapSheet <> "" Then Exit Do

        MsgBox BuildArmpilMapErrorMessage(defaultPairs), vbExclamation, "Mapear lances ARMPIL"
    Loop

    DeleteLanceMapEditorSheet ws
    If Not previousSheet Is Nothing Then
        On Error Resume Next
        previousSheet.Activate
        On Error GoTo 0
    End If
End Function

Public Function PrepareArmpilLanceMapSheet( _
    ByVal allLevelsCsv As String, _
    ByVal identifiedLevelsCsv As String, _
    ByVal defaultMap As String, _
    ByVal promptText As String _
) As Worksheet
    Dim ws As Worksheet
    Dim levelParts() As String
    Dim defaultLances() As String
    Dim levelCount As Long
    Dim i As Long
    Dim rowIndex As Long
    Dim lastDataRow As Long
    Dim normalizedLevel As String
    Dim isUsefulLevel As Boolean
    Dim firstPositiveLance As Long
    Dim buttonTop As Double
    Dim buttonHeight As Double
    Dim buttonWidth As Double

    Set ws = GetOrCreateLanceMapEditorSheet()
    ClearLanceMapEditorSheet ws

    levelParts = Split(allLevelsCsv, ",")
    defaultLances = Split(BuildLanceEntriesForLevels(allLevelsCsv, defaultMap), ",")
    levelCount = UBound(levelParts) - LBound(levelParts) + 1
    lastDataRow = LANCE_MAP_FIRST_DATA_ROW + levelCount - 1
    firstPositiveLance = GetFirstPositiveLanceFromCsv(BuildLanceEntriesForLevels(allLevelsCsv, defaultMap))

    With ws
        .Visible = xlSheetVisible
        .Cells.ClearFormats
        .Cells.Font.Name = "Segoe UI"
        .Cells.Font.Size = 10
        .Columns("A").ColumnWidth = 16
        .Columns("B").ColumnWidth = 31
        .Columns("C").ColumnWidth = 12
        .Columns("D").ColumnWidth = 18
        .Columns("E").ColumnWidth = 14
        .Columns("F").ColumnWidth = 14
        .Columns("G").ColumnWidth = 4
        .Rows("1:4").RowHeight = 24

        With .Range("A1:F1")
            .Merge
            .Value = "Mapear lances ARMPIL"
            .Font.Size = 16
            .Font.Bold = True
            .Font.Color = RGB(255, 255, 255)
            .Interior.Color = RGB(72, 95, 108)
            .HorizontalAlignment = xlLeft
            .VerticalAlignment = xlCenter
            .RowHeight = 34
        End With

        With .Range("A2:F2")
            .Merge
            .Value = "Ajuste apenas o que precisar: edite os lances na tabela ou use um ajuste rapido."
            .Font.Color = RGB(74, 74, 74)
            .Interior.Color = RGB(242, 245, 247)
            .RowHeight = 26
            .WrapText = True
            .VerticalAlignment = xlCenter
        End With

        .Range("A3").Value = "Comando rapido"
        .Range("A3:A4").Font.Bold = True
        .Range("A3:A4").HorizontalAlignment = xlRight
        .Range("A3:A4").VerticalAlignment = xlCenter
        .Range("A3:A4").Interior.Color = RGB(255, 255, 255)
        .Range("A3:A4").Borders.LineStyle = xlContinuous
        .Range("A3:A4").Borders.Color = RGB(220, 226, 230)

        .Range("B3:D3").Merge
        .Range(LANCE_MAP_QUICK_INPUT_CELL).Value = ""
        .Range(LANCE_MAP_QUICK_INPUT_CELL).Interior.Color = RGB(255, 250, 205)
        .Range("B3:D3").Borders.LineStyle = xlContinuous
        .Range("B3:D3").Borders.Color = RGB(220, 226, 230)
        .Range("B3:D3").VerticalAlignment = xlCenter

        .Range("A4").Value = "Primeiro lance"
        .Range(LANCE_MAP_START_CELL).Value = IIf(firstPositiveLance > 0, CStr(firstPositiveLance), "")
        .Range(LANCE_MAP_START_CELL).Interior.Color = RGB(255, 250, 205)
        .Range("B4").HorizontalAlignment = xlCenter
        .Range("B4").Borders.LineStyle = xlContinuous
        .Range("B4").Borders.Color = RGB(220, 226, 230)
        .Range("B4").VerticalAlignment = xlCenter

        .Range("C4:D4").Merge
        .Range("C4").Value = "Ex.: inicio=23"
        .Range("C4").Font.Color = RGB(110, 110, 110)
        .Range("C4:D4").Borders.LineStyle = xlContinuous
        .Range("C4:D4").Borders.Color = RGB(220, 226, 230)
        .Range("C4:D4").VerticalAlignment = xlCenter
        .Range("C4:D4").Interior.Color = RGB(255, 255, 255)

        .Range("E4:F4").Merge
        .Range("E4").Value = "Ou use regras: 1047-1050=12; >1050=15"
        .Range("E4").Font.Color = RGB(110, 110, 110)
        .Range("E4:F4").Borders.LineStyle = xlContinuous
        .Range("E4:F4").Borders.Color = RGB(220, 226, 230)
        .Range("E4:F4").VerticalAlignment = xlCenter
        .Range("E4:F4").Interior.Color = RGB(255, 255, 255)

        .Range("A6").Value = "Nivel superior"
        .Range("B6").Value = "Trecho atendido"
        .Range("C6").Value = "Lance"
        .Range("D6").Value = "Status"
        With .Range("A6:D6")
            .Font.Bold = True
            .Font.Color = RGB(255, 255, 255)
            .Interior.Color = RGB(95, 122, 138)
            .HorizontalAlignment = xlCenter
            .VerticalAlignment = xlCenter
            .RowHeight = 22
        End With

        For i = 0 To levelCount - 1
            rowIndex = LANCE_MAP_FIRST_DATA_ROW + i
            normalizedLevel = NormalizeLevelToken(levelParts(i))
            isUsefulLevel = CsvContainsNormalizedLevel(identifiedLevelsCsv, normalizedLevel)

            .Cells(rowIndex, 1).Value = "+" & normalizedLevel
            .Cells(rowIndex, 2).Value = BuildLevelContext(levelParts, i)
            If i <= UBound(defaultLances) Then .Cells(rowIndex, 3).Value = Trim$(defaultLances(i))
            .Cells(rowIndex, 4).Value = IIf(isUsefulLevel, "Com armadura", "Detectado no PDF")

            With .Range(.Cells(rowIndex, 1), .Cells(rowIndex, 4))
                .Borders.LineStyle = xlContinuous
                .Borders.Color = RGB(220, 226, 230)
                .VerticalAlignment = xlCenter
                .RowHeight = 24
            End With
            .Cells(rowIndex, 1).HorizontalAlignment = xlRight
            .Cells(rowIndex, 2).WrapText = True
            .Cells(rowIndex, 3).HorizontalAlignment = xlCenter
            .Cells(rowIndex, 4).WrapText = True

            .Cells(rowIndex, 3).Interior.Color = RGB(255, 250, 205)
            If isUsefulLevel Then
                .Range(.Cells(rowIndex, 1), .Cells(rowIndex, 4)).Interior.Color = RGB(255, 255, 255)
                .Cells(rowIndex, 3).Interior.Color = RGB(255, 250, 205)
            Else
                .Range(.Cells(rowIndex, 1), .Cells(rowIndex, 4)).Interior.Color = RGB(245, 245, 245)
                .Cells(rowIndex, 3).Interior.Color = RGB(252, 248, 220)
                .Range(.Cells(rowIndex, 1), .Cells(rowIndex, 4)).Font.Color = RGB(120, 120, 120)
            End If
        Next i

        buttonTop = .Range("E3").Top + 1
        buttonHeight = .Range("E3").Height - 2
        buttonWidth = .Range("E3").Width - 6
        AddLanceMapEditorButton ws, "Confirmar", .Range("E3").Left + 3, buttonTop, buttonWidth, buttonHeight, RGB(46, 125, 50), "ArmpilLanceMapEditorConfirm"
        AddLanceMapEditorButton ws, "Cancelar", .Range("F3").Left + 3, buttonTop, buttonWidth, buttonHeight, RGB(117, 117, 117), "ArmpilLanceMapEditorCancel"

        With .Range("A1:F" & lastDataRow)
            .Borders(xlEdgeBottom).Color = RGB(220, 226, 230)
        End With

        .Rows("1:2").EntireRow.AutoFit
        .Rows("3").EntireRow.RowHeight = 28
        .Rows("4").EntireRow.RowHeight = 24
        .Rows("7:8").EntireRow.RowHeight = 8
        .Columns("G").EntireColumn.Hidden = True
        .Activate
        .Range("C" & LANCE_MAP_FIRST_DATA_ROW).Select
    End With

    Set PrepareArmpilLanceMapSheet = ws
End Function

Public Function ReadLanceMapFromEditorSheet(ByVal ws As Worksheet, ByVal levelsCsv As String) As String
    Dim quickText As String
    Dim startText As String
    Dim rawLances As String
    Dim desiredStart As Long

    quickText = Trim$(CStr(ws.Range(LANCE_MAP_QUICK_INPUT_CELL).Value2))
    If quickText <> "" Then
        ReadLanceMapFromEditorSheet = BuildLanceMapFromLists(levelsCsv, quickText)
        Exit Function
    End If

    rawLances = BuildLanceCsvFromEditorSheet(ws, levelsCsv)
    If rawLances = "" Then Exit Function

    startText = Trim$(CStr(ws.Range(LANCE_MAP_START_CELL).Value2))
    If startText <> "" Then
        If Not IsNumeric(startText) Then Exit Function
        desiredStart = CLng(Val(startText))
        If desiredStart <= 0 Then Exit Function
        rawLances = ShiftLanceCsvStart(rawLances, desiredStart)
        If rawLances = "" Then Exit Function
    End If

    ReadLanceMapFromEditorSheet = BuildLanceMapFromLists(levelsCsv, rawLances)
End Function

Public Function BuildLanceCsvFromEditorSheet(ByVal ws As Worksheet, ByVal levelsCsv As String) As String
    Dim levelCount As Long
    Dim i As Long
    Dim rowIndex As Long
    Dim text As String
    Dim lanceValue As Long

    levelCount = CountCsvItems(levelsCsv)
    If levelCount <= 0 Then Exit Function

    For i = 0 To levelCount - 1
        rowIndex = LANCE_MAP_FIRST_DATA_ROW + i
        If i > 0 Then BuildLanceCsvFromEditorSheet = BuildLanceCsvFromEditorSheet & ","

        text = Trim$(CStr(ws.Cells(rowIndex, 3).Value2))
        If text = "" Then
            BuildLanceCsvFromEditorSheet = BuildLanceCsvFromEditorSheet & "0"
            GoTo NextItem
        End If

        If Not IsNumeric(text) Then Exit Function
        lanceValue = CLng(Val(text))
        If lanceValue < 0 Then Exit Function
        BuildLanceCsvFromEditorSheet = BuildLanceCsvFromEditorSheet & CStr(lanceValue)
NextItem:
    Next i
End Function

Public Function GetOrCreateLanceMapEditorSheet() As Worksheet
    On Error Resume Next
    Set GetOrCreateLanceMapEditorSheet = ThisWorkbook.Worksheets(LANCE_MAP_SHEET_NAME)
    On Error GoTo 0

    If GetOrCreateLanceMapEditorSheet Is Nothing Then
        Set GetOrCreateLanceMapEditorSheet = ThisWorkbook.Worksheets.Add(After:=ThisWorkbook.Worksheets(ThisWorkbook.Worksheets.count))
        GetOrCreateLanceMapEditorSheet.Name = LANCE_MAP_SHEET_NAME
    End If
End Function

Public Sub ClearLanceMapEditorSheet(ByVal ws As Worksheet)
    Dim shp As Shape

    ws.Cells.UnMerge
    ws.Cells.Clear
    For Each shp In ws.Shapes
        shp.Delete
    Next shp
End Sub

Public Sub DeleteLanceMapEditorSheet(ByVal ws As Worksheet)
    Dim oldAlerts As Boolean

    If ws Is Nothing Then Exit Sub

    oldAlerts = Application.DisplayAlerts
    Application.DisplayAlerts = False
    On Error Resume Next
    ws.Delete
    On Error GoTo 0
    Application.DisplayAlerts = oldAlerts
End Sub

Public Sub WaitForLanceMapEditorAction(ByVal sheetName As String)
    Do While mLanceMapEditorAction = ""
        DoEvents
        If Not WorksheetIsAvailable(sheetName) Then
            mLanceMapEditorAction = "cancel"
            Exit Do
        End If
    Loop
End Sub

Public Function WorksheetIsAvailable(ByVal sheetName As String) As Boolean
    Dim ws As Worksheet

    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets(sheetName)
    On Error GoTo 0

    WorksheetIsAvailable = Not ws Is Nothing
End Function

Public Function CsvContainsNormalizedLevel(ByVal levelsCsv As String, ByVal normalizedLevel As String) As Boolean
    Dim parts() As String
    Dim i As Long

    If Trim$(levelsCsv) = "" Or Trim$(normalizedLevel) = "" Then Exit Function

    parts = Split(levelsCsv, ",")
    For i = LBound(parts) To UBound(parts)
        If NormalizeLevelToken(parts(i)) = normalizedLevel Then
            CsvContainsNormalizedLevel = True
            Exit Function
        End If
    Next i
End Function

Public Function BuildLevelContext(ByVal levelParts As Variant, ByVal itemIndex As Long) As String
    If itemIndex <= LBound(levelParts) Then
        BuildLevelContext = "Trecho logo abaixo"
    Else
        BuildLevelContext = "+" & NormalizeLevelToken(levelParts(itemIndex - 1)) & " -> +" & NormalizeLevelToken(levelParts(itemIndex))
    End If
End Function

Public Function GetFirstPositiveLanceFromCsv(ByVal lancesCsv As String) As Long
    Dim parts() As String
    Dim i As Long
    Dim token As String

    If Trim$(lancesCsv) = "" Then Exit Function

    parts = Split(lancesCsv, ",")
    For i = LBound(parts) To UBound(parts)
        token = Trim$(parts(i))
        If token <> "" And IsNumeric(token) Then
            GetFirstPositiveLanceFromCsv = CLng(Val(token))
            If GetFirstPositiveLanceFromCsv > 0 Then Exit Function
        End If
    Next i

    GetFirstPositiveLanceFromCsv = 0
End Function

Public Sub AddLanceMapEditorButton( _
    ByVal ws As Worksheet, _
    ByVal captionText As String, _
    ByVal leftPos As Double, _
    ByVal topPos As Double, _
    ByVal widthPos As Double, _
    ByVal heightPos As Double, _
    ByVal fillColor As Long, _
    ByVal macroName As String _
)
    Dim shp As Shape

    Set shp = ws.Shapes.AddShape(msoShapeRoundedRectangle, leftPos, topPos, widthPos, heightPos)
    With shp
        .Name = "btn_" & Replace(captionText, " ", "_")
        .Fill.ForeColor.RGB = fillColor
        .Line.Visible = msoFalse
        .TextFrame2.TextRange.Characters.Text = captionText
        .TextFrame2.TextRange.Font.Size = 10
        .TextFrame2.TextRange.Font.Fill.ForeColor.RGB = RGB(255, 255, 255)
        .TextFrame2.VerticalAnchor = msoAnchorMiddle
        .TextFrame2.TextRange.ParagraphFormat.Alignment = msoAlignCenter
        .OnAction = "'" & ThisWorkbook.Name & "'!" & macroName
    End With
End Sub

Public Sub ArmpilLanceMapEditorConfirm()
    mLanceMapEditorAction = "confirm"
End Sub

Public Sub ArmpilLanceMapEditorCancel()
    mLanceMapEditorAction = "cancel"
End Sub

Public Function TryBuildShiftedLanceMapFromStart(ByVal levelsCsv As String, ByVal rawText As String, ByRef mapText As String) As Boolean
    Dim desiredStart As Long
    Dim suggestedLances As String
    Dim shiftedLances As String

    If Not TryParseStartLanceOverride(rawText, desiredStart) Then Exit Function

    suggestedLances = GetSuggestedArmpilLances(levelsCsv)
    If Trim$(suggestedLances) = "" Then Exit Function

    shiftedLances = ShiftLanceCsvStart(suggestedLances, desiredStart)
    If Trim$(shiftedLances) = "" Then Exit Function

    mapText = BuildLanceMapFromLists(levelsCsv, shiftedLances)
    TryBuildShiftedLanceMapFromStart = (Trim$(mapText) <> "")
End Function

Public Function TryParseStartLanceOverride(ByVal rawText As String, ByRef desiredStart As Long) As Boolean
    Dim normalized As String
    Dim parts() As String
    Dim i As Long
    Dim chunk As String
    Dim sepPos As Long
    Dim keyText As String
    Dim valueText As String

    normalized = LCase$(Trim$(rawText))
    If normalized = "" Then Exit Function

    normalized = Replace(normalized, "comeca", "inicio")
    normalized = Replace(normalized, "lance inicial", "inicio")
    normalized = Replace(normalized, "inicia", "inicio")
    normalized = Replace(normalized, "start", "inicio")
    normalized = Replace(normalized, "primeiro lance", "inicio")
    normalized = Replace(normalized, vbCrLf, ";")
    normalized = Replace(normalized, vbCr, ";")
    normalized = Replace(normalized, vbLf, ";")

    parts = Split(normalized, ";")
    For i = LBound(parts) To UBound(parts)
        chunk = Trim$(parts(i))
        If chunk = "" Then GoTo NextChunk

        sepPos = InStr(1, chunk, "=", vbTextCompare)
        If sepPos = 0 Then sepPos = InStr(1, chunk, ":", vbTextCompare)
        If sepPos <= 1 Or sepPos >= Len(chunk) Then GoTo NextChunk

        keyText = Trim$(Left$(chunk, sepPos - 1))
        valueText = Trim$(Mid$(chunk, sepPos + 1))
        keyText = Replace(keyText, " ", "")
        keyText = Replace(keyText, "-", "")
        keyText = Replace(keyText, "_", "")

        If keyText = "inicio" Or keyText = "primeirolance" Or keyText = "lanceinicial" Then
            If Not IsNumeric(valueText) Then Exit Function
            desiredStart = CLng(Val(valueText))
            If desiredStart <= 0 Then Exit Function
            TryParseStartLanceOverride = True
            Exit Function
        End If
NextChunk:
    Next i
End Function

Public Function ShiftLanceCsvStart(ByVal lancesCsv As String, ByVal desiredStart As Long) As String
    Dim parts() As String
    Dim i As Long
    Dim token As String
    Dim currentStart As Long
    Dim offset As Long
    Dim shiftedValue As Long

    If desiredStart <= 0 Then Exit Function
    If Trim$(lancesCsv) = "" Then Exit Function

    lancesCsv = Replace(lancesCsv, ";", ",")
    lancesCsv = Replace(lancesCsv, vbCrLf, ",")
    lancesCsv = Replace(lancesCsv, vbCr, ",")
    lancesCsv = Replace(lancesCsv, vbLf, ",")
    parts = Split(lancesCsv, ",")

    currentStart = 0
    For i = LBound(parts) To UBound(parts)
        token = Trim$(parts(i))
        If token <> "" And IsNumeric(token) Then
            currentStart = CLng(Val(token))
            If currentStart > 0 Then Exit For
        End If
    Next i

    If currentStart <= 0 Then Exit Function
    offset = desiredStart - currentStart

    For i = LBound(parts) To UBound(parts)
        If i > LBound(parts) Then ShiftLanceCsvStart = ShiftLanceCsvStart & ","

        token = Trim$(parts(i))
        If token = "" Then GoTo NextValue
        If Not IsNumeric(token) Then Exit Function

        shiftedValue = CLng(Val(token))
        If shiftedValue > 0 Then
            shiftedValue = shiftedValue + offset
            If shiftedValue < 0 Then Exit Function
            ShiftLanceCsvStart = ShiftLanceCsvStart & CStr(shiftedValue)
        Else
            ShiftLanceCsvStart = ShiftLanceCsvStart & CStr(shiftedValue)
        End If
NextValue:
    Next i
End Function

Public Function ContainsLanceRuleSyntax(ByVal rawText As String) As Boolean
    Dim normalized As String

    normalized = LCase$(Trim$(rawText))
    If normalized = "" Then Exit Function

    If InStr(normalized, ">") > 0 Or InStr(normalized, "<") > 0 Then
        ContainsLanceRuleSyntax = True
        Exit Function
    End If

    If HasNumericRangeRule(normalized, "-") Then
        ContainsLanceRuleSyntax = True
        Exit Function
    End If

    If HasNumericRangeRule(normalized, " ate ") Then
        ContainsLanceRuleSyntax = True
    End If
End Function

Public Function HasNumericRangeRule(ByVal rawText As String, ByVal separatorText As String) As Boolean
    Dim parts() As String
    Dim i As Long
    Dim chunk As String
    Dim sepPos As Long
    Dim candidate As String
    Dim ruleText As String
    Dim dummyValue As Double

    rawText = Replace(rawText, "->", "=")
    rawText = Replace(rawText, "=>", "=")
    rawText = Replace(rawText, vbCrLf, ";")
    rawText = Replace(rawText, vbCr, ";")
    rawText = Replace(rawText, vbLf, ";")

    parts = Split(rawText, ";")
    For i = LBound(parts) To UBound(parts)
        chunk = Trim$(parts(i))
        If chunk = "" Then GoTo NextChunk

        sepPos = InStr(1, chunk, "=", vbTextCompare)
        If InStr(1, chunk, ":", vbTextCompare) > 0 Then
            sepPos = InStr(1, chunk, ":", vbTextCompare)
            If sepPos > 0 Then
                ruleText = Trim$(Mid$(chunk, sepPos + 1))
            End If
        ElseIf sepPos > 0 Then
            ruleText = Trim$(Left$(chunk, sepPos - 1))
        Else
            ruleText = chunk
        End If

        candidate = NormalizeRuleText(ruleText)
        If InStr(candidate, separatorText) > 0 Then
            If TryParseRangeRule(candidate, dummyValue, dummyValue) Then
                HasNumericRangeRule = True
                Exit Function
            End If
        End If
NextChunk:
    Next i
End Function

Public Function BuildLanceMapFromRules(ByVal levelsCsv As String, ByVal rawText As String) As String
    Dim dict As Object
    Dim levelParts() As String
    Dim i As Long
    Dim normalizedLevel As String
    Dim levelValue As Double
    Dim hasNumericLevel As Boolean
    Dim matchCount As Long

    If Trim$(levelsCsv) = "" Or Trim$(rawText) = "" Then Exit Function

    Set dict = CreateObject("Scripting.Dictionary")
    levelParts = Split(levelsCsv, ",")

    If Not ApplyLanceRuleChunks(levelParts, rawText, dict, matchCount) Then Exit Function
    If matchCount <= 0 Then Exit Function

    For i = LBound(levelParts) To UBound(levelParts)
        normalizedLevel = NormalizeLevelToken(levelParts(i))
        If normalizedLevel = "" Then GoTo NextLevel

        hasNumericLevel = TryParseLevelNumber(normalizedLevel, levelValue)
        If dict.Exists(normalizedLevel) Then
            If CLng(dict(normalizedLevel)) > 0 Then
                If BuildLanceMapFromRules <> "" Then BuildLanceMapFromRules = BuildLanceMapFromRules & ";"
                BuildLanceMapFromRules = BuildLanceMapFromRules & normalizedLevel & "=" & CLng(dict(normalizedLevel))
            End If
        ElseIf hasNumericLevel Then
            ' leave unmapped levels out of the explicit map
        End If
NextLevel:
    Next i
End Function

Public Function ApplyLanceRuleChunks(ByVal levelParts As Variant, ByVal rawText As String, ByRef dict As Object, ByRef matchCount As Long) As Boolean
    Dim normalized As String
    Dim parts() As String
    Dim i As Long
    Dim chunk As String
    Dim ruleText As String
    Dim lanceValue As Long

    normalized = Trim$(rawText)
    normalized = Replace(normalized, "->", "=")
    normalized = Replace(normalized, "=>", "=")
    normalized = Replace(normalized, vbCrLf, ";")
    normalized = Replace(normalized, vbCr, ";")
    normalized = Replace(normalized, vbLf, ";")

    parts = Split(normalized, ";")
    For i = LBound(parts) To UBound(parts)
        chunk = Trim$(parts(i))
        If chunk = "" Then GoTo NextChunk

        If Not TryParseLanceRuleChunk(chunk, ruleText, lanceValue) Then Exit Function
        If Not ApplySingleLanceRule(levelParts, ruleText, lanceValue, dict, matchCount) Then Exit Function
NextChunk:
    Next i

    ApplyLanceRuleChunks = True
End Function

Public Function TryParseLanceRuleChunk(ByVal chunk As String, ByRef ruleText As String, ByRef lanceValue As Long) As Boolean
    Dim sepPos As Long
    Dim leftText As String
    Dim rightText As String

    sepPos = InStr(1, chunk, ":", vbTextCompare)
    If sepPos > 0 Then
        leftText = Trim$(Left$(chunk, sepPos - 1))
        rightText = Trim$(Mid$(chunk, sepPos + 1))
        If Not IsNumeric(leftText) Then Exit Function
        lanceValue = CLng(Val(leftText))
        ruleText = Trim$(rightText)
        TryParseLanceRuleChunk = (ruleText <> "")
        Exit Function
    End If

    sepPos = InStr(1, chunk, "=", vbTextCompare)
    If sepPos <= 1 Or sepPos >= Len(chunk) Then Exit Function

    leftText = Trim$(Left$(chunk, sepPos - 1))
    rightText = Trim$(Mid$(chunk, sepPos + 1))
    If Not IsNumeric(rightText) Then Exit Function

    ruleText = Trim$(leftText)
    lanceValue = CLng(Val(rightText))
    TryParseLanceRuleChunk = (ruleText <> "")
End Function

Public Function ApplySingleLanceRule(ByVal levelParts As Variant, ByVal ruleText As String, ByVal lanceValue As Long, ByRef dict As Object, ByRef matchCount As Long) As Boolean
    Dim i As Long
    Dim normalizedLevel As String
    Dim levelValue As Double
    Dim matched As Boolean
    Dim validRule As Boolean

    ruleText = NormalizeRuleText(ruleText)
    If ruleText = "" Then Exit Function

    For i = LBound(levelParts) To UBound(levelParts)
        normalizedLevel = NormalizeLevelToken(levelParts(i))
        If normalizedLevel = "" Then GoTo NextLevel
        If Not TryParseLevelNumber(normalizedLevel, levelValue) Then GoTo NextLevel

        If MatchLevelRule(levelValue, ruleText, validRule) Then
            If lanceValue > 0 Then
                dict(normalizedLevel) = lanceValue
            ElseIf dict.Exists(normalizedLevel) Then
                dict.Remove normalizedLevel
            End If
            matchCount = matchCount + 1
            matched = True
        ElseIf Not validRule Then
            Exit Function
        End If
NextLevel:
    Next i

    ApplySingleLanceRule = matched
End Function

Public Function NormalizeRuleText(ByVal ruleText As String) As String
    ruleText = LCase$(Trim$(ruleText))
    If Left$(ruleText, 3) = "de " Then ruleText = Trim$(Mid$(ruleText, 4))
    ruleText = Replace(ruleText, ",", ".")
    ruleText = Replace(ruleText, " ate ", "-")
    NormalizeRuleText = Trim$(ruleText)
End Function

Public Function MatchLevelRule(ByVal levelValue As Double, ByVal ruleText As String, ByRef validRule As Boolean) As Boolean
    Dim startValue As Double
    Dim endValue As Double
    Dim compareValue As Double
    Dim tailText As String

    validRule = True
    If ruleText = "" Then
        validRule = False
        Exit Function
    End If

    If Right$(ruleText, 2) = "<=" Then
        tailText = Trim$(Left$(ruleText, Len(ruleText) - 2))
        If Not TryParseLevelNumber(tailText, compareValue) Then validRule = False: Exit Function
        MatchLevelRule = (levelValue >= compareValue)
        Exit Function
    End If

    If Right$(ruleText, 2) = ">=" Then
        tailText = Trim$(Left$(ruleText, Len(ruleText) - 2))
        If Not TryParseLevelNumber(tailText, compareValue) Then validRule = False: Exit Function
        MatchLevelRule = (levelValue <= compareValue)
        Exit Function
    End If

    If Right$(ruleText, 1) = "<" Then
        tailText = Trim$(Left$(ruleText, Len(ruleText) - 1))
        If Not TryParseLevelNumber(tailText, compareValue) Then validRule = False: Exit Function
        MatchLevelRule = (levelValue > compareValue)
        Exit Function
    End If

    If Right$(ruleText, 1) = ">" Then
        tailText = Trim$(Left$(ruleText, Len(ruleText) - 1))
        If Not TryParseLevelNumber(tailText, compareValue) Then validRule = False: Exit Function
        MatchLevelRule = (levelValue < compareValue)
        Exit Function
    End If

    If Left$(ruleText, 2) = ">=" Then
        If Not TryParseLevelNumber(Mid$(ruleText, 3), compareValue) Then validRule = False: Exit Function
        MatchLevelRule = (levelValue >= compareValue)
        Exit Function
    End If

    If Left$(ruleText, 2) = "<=" Then
        If Not TryParseLevelNumber(Mid$(ruleText, 3), compareValue) Then validRule = False: Exit Function
        MatchLevelRule = (levelValue <= compareValue)
        Exit Function
    End If

    If Left$(ruleText, 1) = ">" Then
        If Not TryParseLevelNumber(Mid$(ruleText, 2), compareValue) Then validRule = False: Exit Function
        MatchLevelRule = (levelValue > compareValue)
        Exit Function
    End If

    If Left$(ruleText, 1) = "<" Then
        If Not TryParseLevelNumber(Mid$(ruleText, 2), compareValue) Then validRule = False: Exit Function
        MatchLevelRule = (levelValue < compareValue)
        Exit Function
    End If

    If TryParseRangeRule(ruleText, startValue, endValue) Then
        MatchLevelRule = (levelValue >= startValue And levelValue <= endValue)
        Exit Function
    End If

    If TryParseLevelNumber(ruleText, compareValue) Then
        MatchLevelRule = (Abs(levelValue - compareValue) < 0.0001)
        Exit Function
    End If

    validRule = False
End Function

Public Function TryParseRangeRule(ByVal ruleText As String, ByRef startValue As Double, ByRef endValue As Double) As Boolean
    Dim sepPos As Long
    Dim leftText As String
    Dim rightText As String

    ruleText = NormalizeRuleText(ruleText)
    sepPos = InStr(1, ruleText, "-", vbTextCompare)
    If sepPos <= 1 Or sepPos >= Len(ruleText) Then Exit Function

    leftText = Trim$(Left$(ruleText, sepPos - 1))
    rightText = Trim$(Mid$(ruleText, sepPos + 1))
    If Not TryParseLevelNumber(leftText, startValue) Then Exit Function
    If Not TryParseLevelNumber(rightText, endValue) Then Exit Function
    If endValue < startValue Then Exit Function

    TryParseRangeRule = True
End Function

Public Function TryParseLevelNumber(ByVal rawText As String, ByRef valueOut As Double) As Boolean
    Dim normalized As String

    normalized = NormalizeLevelToken(rawText)
    If normalized = "" Then Exit Function
    If Not IsNumeric(normalized) Then Exit Function

    valueOut = CDbl(Val(normalized))
    TryParseLevelNumber = True
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
        "Se a sequencia estiver certa e so mudou o inicio, informe apenas inicio=23." & vbCrLf & _
        "Tambem aceita regras por faixa. Ex.: 1047-1050=12; >1050=15; 1050<=15" & vbCrLf & _
        "Ex.: " & IIf(Trim$(defaultPairs) <> "", defaultPairs, "6:+1043.40; 7:+1046.60")
End Function

Public Function BuildArmpilMapErrorMessage(ByVal defaultPairs As String) As String
    BuildArmpilMapErrorMessage = _
        "Entrada invalida." & vbCrLf & vbCrLf & _
        "Use uma destas opcoes:" & vbCrLf & _
        "1. Pares no formato lance:nivel." & vbCrLf & _
        "   Use lance 0 para ignorar. Ex.: " & IIf(Trim$(defaultPairs) <> "", defaultPairs, "0:+1040.25; 6:+1043.40; 7:+1046.60") & vbCrLf & vbCrLf & _
        "2. Somente os lances na ordem dos niveis, separados por virgula." & vbCrLf & _
        "   Ex.: 0,6,7,8" & vbCrLf & vbCrLf & _
        "3. Ajuste apenas o primeiro lance da sequencia sugerida." & vbCrLf & _
        "   Ex.: inicio=23" & vbCrLf & vbCrLf & _
        "4. Regras por faixa ou comparacao." & vbCrLf & _
        "   Ex.: 1047-1050=12; >1050=15; 1050<=15"
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

Public Sub SaveStoredArmpilLanceLevelMap(ByVal mapText As String)
    Dim safeText As String

    ClearStoredArmpilLanceLevelMap
    If Trim$(mapText) = "" Then Exit Sub

    safeText = Replace(mapText, Chr$(34), Chr$(34) & Chr$(34))
    ThisWorkbook.Names.Add Name:=ARMPIL_LANCE_MAP_NAME, RefersTo:="=""" & safeText & """"
End Sub

Public Sub ClearStoredArmpilLanceLevelMap()
    On Error Resume Next
    ThisWorkbook.Names(ARMPIL_LANCE_MAP_NAME).Delete
    On Error GoTo 0
End Sub

Public Function GetStoredArmpilLanceLevelMap() As String
    Dim rawRefersTo As String

    On Error Resume Next
    rawRefersTo = ThisWorkbook.Names(ARMPIL_LANCE_MAP_NAME).RefersTo
    On Error GoTo 0

    rawRefersTo = Trim$(rawRefersTo)
    If rawRefersTo = "" Then Exit Function

    If Left$(rawRefersTo, 1) = "=" Then rawRefersTo = Mid$(rawRefersTo, 2)
    If Left$(rawRefersTo, 1) = Chr$(34) And Right$(rawRefersTo, 1) = Chr$(34) Then
        rawRefersTo = Mid$(rawRefersTo, 2, Len(rawRefersTo) - 2)
    End If

    GetStoredArmpilLanceLevelMap = Replace(rawRefersTo, Chr$(34) & Chr$(34), Chr$(34))
End Function

Public Function BuildArmpilLevelDisplayDict() As Object
    Dim dict As Object
    Dim mapText As String
    Dim parts() As String
    Dim i As Long
    Dim chunk As String
    Dim sepPos As Long
    Dim levelText As String
    Dim lanceText As String
    Dim normalizedLevel As String
    Dim normalizedLance As String

    Set dict = CreateObject("Scripting.Dictionary")
    mapText = GetStoredArmpilLanceLevelMap()
    If Trim$(mapText) = "" Then
        Set BuildArmpilLevelDisplayDict = dict
        Exit Function
    End If

    parts = Split(mapText, ";")
    For i = LBound(parts) To UBound(parts)
        chunk = Trim$(parts(i))
        If chunk = "" Then GoTo NextItem

        sepPos = InStr(1, chunk, "=", vbTextCompare)
        If sepPos <= 1 Or sepPos >= Len(chunk) Then GoTo NextItem

        levelText = Trim$(Left$(chunk, sepPos - 1))
        lanceText = Trim$(Mid$(chunk, sepPos + 1))
        normalizedLevel = NormalizeLevelToken(levelText)
        normalizedLance = Trim$(CStr(CLng(Val(lanceText))))

        If normalizedLevel <> "" And normalizedLance <> "" Then
            If Not dict.Exists(normalizedLance) Then dict.Add normalizedLance, Replace(normalizedLevel, ".", ",")
        End If
NextItem:
    Next i

    Set BuildArmpilLevelDisplayDict = dict
End Function

Public Function GetDisplayLevelForLance(ByVal lanceValue As Variant, Optional ByVal levelDict As Object = Nothing) As String
    Dim normalizedLance As String

    normalizedLance = Trim$(CStr(lanceValue))
    If normalizedLance = "" Then Exit Function

    If levelDict Is Nothing Then Set levelDict = BuildArmpilLevelDisplayDict()
    If Not levelDict Is Nothing Then
        If levelDict.Exists(normalizedLance) Then
            GetDisplayLevelForLance = CStr(levelDict(normalizedLance))
            Exit Function
        End If
    End If

    GetDisplayLevelForLance = normalizedLance
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

Public Function GetKnownPilarLancesForPython() As String
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim data As Variant
    Dim groups As Object
    Dim i As Long
    Dim pilarName As String
    Dim lanceValue As String
    Dim key As Variant
    Dim values As Variant

    Set ws = ThisWorkbook.Sheets("SELE")
    lastRow = ws.Cells(ws.Rows.count, 3).End(xlUp).Row
    If lastRow < 6 Then Exit Function

    data = ws.Range(ws.Cells(6, 2), ws.Cells(lastRow, 3)).Value2
    Set groups = CreateObject("Scripting.Dictionary")

    If IsArray(data) Then
        For i = 1 To UBound(data, 1)
            pilarName = NormalizePilarName(CStr(data(i, 1)))
            lanceValue = Trim$(CStr(data(i, 2)))
            If pilarName = "" Or lanceValue = "" Then GoTo NextRow
            If Not IsNumeric(lanceValue) Then GoTo NextRow

            If Not groups.Exists(pilarName) Then
                Set groups(pilarName) = CreateObject("Scripting.Dictionary")
            End If
            groups(pilarName)(CLng(lanceValue)) = True
NextRow:
        Next i
    End If

    For Each key In groups.keys
        values = groups(key).keys
        SortNumericVariantArray values
        If GetKnownPilarLancesForPython <> "" Then GetKnownPilarLancesForPython = GetKnownPilarLancesForPython & ";"
        GetKnownPilarLancesForPython = GetKnownPilarLancesForPython & CStr(key) & "=" & JoinVariantList(values)
    Next key
End Function
