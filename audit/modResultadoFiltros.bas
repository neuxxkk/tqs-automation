Option Explicit

' ================================================================
' modResultadoFiltros
' ================================================================

Private Const RESULTADO_SHEET_NAME As String = "RESULTADO"
Private Const RESULTADO_TABLE_NAME As String = "Tabela1"
Private Const STATUS_OPEN_CELL As String = "M13"
Private Const PROC_OPEN_CELL As String = "M14"
Private Const CHECK_MARK_CODE As Long = 10003
Private Const FILTER_MESSAGE_CELL As String = "H6"

Public Sub InicializarFiltrosResultado(Optional ByVal resetSelections As Boolean = False)
    Dim ws As Worksheet
    Set ws = GetRequiredWorksheet(RESULTADO_SHEET_NAME)

    EnsureResultadoFilterState ws, resetSelections
    BindResultadoFilterShapes ws
    SyncResultadoFilterUi ws
End Sub

Public Sub ToggleDropdown(ByVal qual As String)
    Dim ws As Worksheet
    Set ws = GetRequiredWorksheet(RESULTADO_SHEET_NAME)

    EnsureResultadoFilterState ws, False
    BindResultadoFilterShapes ws

    Select Case UCase$(Trim$(qual))
        Case "STATUS"
            ws.Range(STATUS_OPEN_CELL).Value = Not GetBooleanCellValue(ws.Range(STATUS_OPEN_CELL), False)
            If CBool(ws.Range(STATUS_OPEN_CELL).Value) Then ws.Range(PROC_OPEN_CELL).Value = False
        Case "PROCESSAMENTO"
            ws.Range(PROC_OPEN_CELL).Value = Not GetBooleanCellValue(ws.Range(PROC_OPEN_CELL), False)
            If CBool(ws.Range(PROC_OPEN_CELL).Value) Then ws.Range(STATUS_OPEN_CELL).Value = False
        Case Else
            Exit Sub
    End Select

    SyncResultadoFilterUi ws
End Sub

Public Sub FecharDropdownsResultado()
    Dim ws As Worksheet
    Dim hadOpenPanel As Boolean

    Set ws = GetRequiredWorksheet(RESULTADO_SHEET_NAME)
    EnsureResultadoFilterState ws, False

    hadOpenPanel = GetBooleanCellValue(ws.Range(STATUS_OPEN_CELL), False) _
        Or GetBooleanCellValue(ws.Range(PROC_OPEN_CELL), False)

    If Not hadOpenPanel Then Exit Sub

    ws.Range(STATUS_OPEN_CELL).Value = False
    ws.Range(PROC_OPEN_CELL).Value = False
    SyncResultadoFilterUi ws
End Sub

Public Sub ToggleCheckbox()
    Dim ws As Worksheet
    Dim callerName As String
    Dim stateCell As Range
    Dim checkboxShapeName As String

    Set ws = GetRequiredWorksheet(RESULTADO_SHEET_NAME)
    EnsureResultadoFilterState ws, False
    BindResultadoFilterShapes ws

    callerName = CStr(Application.Caller)
    Set stateCell = ResolveCheckboxStateCell(ws, callerName, checkboxShapeName)
    If stateCell Is Nothing Then Exit Sub

    stateCell.Value = Not GetBooleanCellValue(stateCell, True)
    SyncCheckboxShape ws, checkboxShapeName, CBool(stateCell.Value)
    ApplyResultadoFiltersCore
End Sub

Public Sub AplicarFiltro()
    ApplyResultadoFiltersCore
End Sub

Public Sub ReaplicarFiltrosResultado()
    ApplyResultadoFiltersCore
End Sub

Public Sub LimparFiltro()
    Dim ws As Worksheet

    Set ws = GetRequiredWorksheet(RESULTADO_SHEET_NAME)
    EnsureResultadoFilterState ws, True
    BindResultadoFilterShapes ws
    SyncResultadoFilterUi ws

    ApplyResultadoFiltersCore
End Sub

Private Sub ApplyResultadoFiltersCore()
    Dim ws As Worksheet
    Dim lo As ListObject
    Dim previousScreenUpdating As Boolean
    Dim lastDataRow As Long
    Dim visibleCount As Long
    Dim rowIndex As Long
    Dim firstRow As Long

    Set ws = GetRequiredWorksheet(RESULTADO_SHEET_NAME)
    Set lo = GetResultadoTable(ws)

    EnsureResultadoFilterState ws, False
    BindResultadoFilterShapes ws

    previousScreenUpdating = Application.ScreenUpdating
    Application.ScreenUpdating = False

    On Error GoTo Cleanup

    firstRow = RESULT_FIRST_DATA_ROW
    lastDataRow = GetResultadoLastDataRow(ws, lo)
    If lastDataRow < firstRow Then lastDataRow = firstRow - 1
    If lastDataRow < firstRow Then GoTo Cleanup

    ClearResultadoFilters ws, lo
    ws.Rows(firstRow & ":" & lastDataRow).Hidden = False

    For rowIndex = firstRow To lastDataRow
        If RowShouldBeVisible(ws, rowIndex, lastDataRow) Then
            ws.Rows(rowIndex).Hidden = False
            visibleCount = visibleCount + 1
        Else
            ws.Rows(rowIndex).Hidden = True
        End If
    Next rowIndex

    If visibleCount = 0 Then
        ws.Rows(firstRow & ":" & lastDataRow).Hidden = False
        SetFiltroMensagem ws, "Nenhum pilar atende aos filtros selecionados."
    Else
        SetFiltroMensagem ws, ""
    End If

    SyncResultadoFilterUi ws

Cleanup:
    Application.ScreenUpdating = previousScreenUpdating
    If Err.Number <> 0 Then
        MsgBox "Erro ao aplicar os filtros do RESULTADO: " & Err.Description, vbExclamation
    End If
End Sub

Private Function RowShouldBeVisible(ByVal ws As Worksheet, ByVal rowIndex As Long, ByVal lastDataRow As Long) As Boolean
    If rowIndex > lastDataRow Then Exit Function
    If Trim$(CStr(ws.Cells(rowIndex, 2).Value2)) = "" Then Exit Function

    RowShouldBeVisible = RowMatchesStatus(ws.Cells(rowIndex, 10).Value2, ws) _
        And RowMatchesProcessamento(ws.Cells(rowIndex, 7).Value2, ws.Cells(rowIndex, 8).Value2, ws)
End Function

Private Function RowMatchesStatus(ByVal rawStatus As Variant, ByVal ws As Worksheet) As Boolean
    Dim selectedCount As Long
    Dim normalizedStatus As String

    selectedCount = CountCheckedStates(ws, Array("M3", "M4", "M5", "M6"))
    If selectedCount = 0 Or selectedCount = 4 Then
        RowMatchesStatus = True
        Exit Function
    End If

    normalizedStatus = NormalizeStatusValue(rawStatus)

    Select Case normalizedStatus
        Case "APROVADO"
            RowMatchesStatus = GetBooleanCellValue(ws.Range("M3"), True)
        Case "MARGEM 15%"
            RowMatchesStatus = GetBooleanCellValue(ws.Range("M4"), True)
        Case "REPROVADO"
            RowMatchesStatus = GetBooleanCellValue(ws.Range("M5"), True)
        Case "SEM MATCH", "NAO DIMENSIONADO"
            RowMatchesStatus = GetBooleanCellValue(ws.Range("M6"), True)
        Case Else
            RowMatchesStatus = False
    End Select
End Function

Private Function RowMatchesProcessamento(ByVal asProjValue As Variant, ByVal asMinValue As Variant, ByVal ws As Worksheet) As Boolean
    Dim selectedCount As Long
    Dim processamento As String

    selectedCount = CountCheckedStates(ws, Array("M8", "M9", "M10", "M11"))
    If selectedCount = 0 Or selectedCount = 4 Then
        RowMatchesProcessamento = True
        Exit Function
    End If

    processamento = GetProcessamentoValue(asProjValue, asMinValue)

    Select Case processamento
        Case "COMPLETO"
            RowMatchesProcessamento = GetBooleanCellValue(ws.Range("M8"), True)
        Case "SOMENTE ARMPIL"
            RowMatchesProcessamento = GetBooleanCellValue(ws.Range("M9"), True)
        Case "SOMENTE SELE"
            RowMatchesProcessamento = GetBooleanCellValue(ws.Range("M10"), True)
        Case "NENHUM"
            RowMatchesProcessamento = GetBooleanCellValue(ws.Range("M11"), True)
        Case Else
            RowMatchesProcessamento = False
    End Select
End Function

Private Function GetProcessamentoValue(ByVal asProjValue As Variant, ByVal asMinValue As Variant) As String
    Dim hasAsProj As Boolean
    Dim hasAsMin As Boolean

    hasAsProj = HasCellContent(asProjValue)
    hasAsMin = HasCellContent(asMinValue)

    Select Case True
        Case hasAsProj And hasAsMin
            GetProcessamentoValue = "COMPLETO"
        Case hasAsProj And Not hasAsMin
            GetProcessamentoValue = "SOMENTE ARMPIL"
        Case Not hasAsProj And hasAsMin
            GetProcessamentoValue = "SOMENTE SELE"
        Case Else
            GetProcessamentoValue = "NENHUM"
    End Select
End Function

Private Function HasCellContent(ByVal value As Variant) As Boolean
    If IsError(value) Or IsNull(value) Or IsEmpty(value) Then Exit Function
    HasCellContent = Trim$(CStr(value)) <> ""
End Function

Private Function NormalizeStatusValue(ByVal value As Variant) As String
    NormalizeStatusValue = UCase$(Trim$(CStr(value)))
End Function

Private Function CountCheckedStates(ByVal ws As Worksheet, ByVal addresses As Variant) As Long
    Dim item As Variant

    For Each item In addresses
        If GetBooleanCellValue(ws.Range(CStr(item)), True) Then
            CountCheckedStates = CountCheckedStates + 1
        End If
    Next item
End Function

Private Sub EnsureResultadoFilterState(ByVal ws As Worksheet, ByVal resetSelections As Boolean)
    Dim addr As Variant

    For Each addr In Array("M3", "M4", "M5", "M6", "M8", "M9", "M10", "M11")
        If resetSelections Or IsEmpty(ws.Range(CStr(addr)).Value) Or Trim$(CStr(ws.Range(CStr(addr)).Value)) = "" Then
            ws.Range(CStr(addr)).Value = True
        End If
    Next addr

    For Each addr In Array(STATUS_OPEN_CELL, PROC_OPEN_CELL)
        If resetSelections Or IsEmpty(ws.Range(CStr(addr)).Value) Or Trim$(CStr(ws.Range(CStr(addr)).Value)) = "" Then
            ws.Range(CStr(addr)).Value = False
        End If
    Next addr
End Sub

Private Sub SyncResultadoFilterUi(ByVal ws As Worksheet)
    SyncCheckboxShape ws, "cbStatus_Aprovado", GetBooleanCellValue(ws.Range("M3"), True)
    SyncCheckboxShape ws, "cbStatus_MargemQuinze", GetBooleanCellValue(ws.Range("M4"), True)
    SyncCheckboxShape ws, "cbStatus_Reprovado", GetBooleanCellValue(ws.Range("M5"), True)
    SyncCheckboxShape ws, "cbStatus_SemMatch", GetBooleanCellValue(ws.Range("M6"), True)
    SyncCheckboxShape ws, "cbProc_Completo", GetBooleanCellValue(ws.Range("M8"), True)
    SyncCheckboxShape ws, "cbProc_SoARMPIL", GetBooleanCellValue(ws.Range("M9"), True)
    SyncCheckboxShape ws, "cbProc_SoSELE", GetBooleanCellValue(ws.Range("M10"), True)
    SyncCheckboxShape ws, "cbProc_Nenhum", GetBooleanCellValue(ws.Range("M11"), True)

    SetStatusPanelVisibility ws, GetBooleanCellValue(ws.Range(STATUS_OPEN_CELL), False)
    SetProcPanelVisibility ws, GetBooleanCellValue(ws.Range(PROC_OPEN_CELL), False)
End Sub

Private Sub SetStatusPanelVisibility(ByVal ws As Worksheet, ByVal isVisible As Boolean)
    Dim shapeName As Variant

    For Each shapeName In Array( _
        "pnlStatus_BG", _
        "cbStatus_Aprovado", _
        "cbStatus_MargemQuinze", _
        "cbStatus_Reprovado", _
        "cbStatus_SemMatch", _
        "lblStatus_Aprovado", _
        "lblStatus_MargemQuinze", _
        "lblStatus_Reprovado", _
        "lblStatus_SemMatch")
        SetShapeVisibleIfExists ws, CStr(shapeName), isVisible
    Next shapeName
End Sub

Private Sub SetProcPanelVisibility(ByVal ws As Worksheet, ByVal isVisible As Boolean)
    Dim shapeName As Variant

    For Each shapeName In Array( _
        "pnlProc_BG", _
        "cbProc_Completo", _
        "cbProc_SoARMPIL", _
        "cbProc_SoSELE", _
        "cbProc_Nenhum", _
        "lblProc_Completo", _
        "lblProc_SoARMPIL", _
        "lblProc_SoSELE", _
        "lblProc_Nenhum")
        SetShapeVisibleIfExists ws, CStr(shapeName), isVisible
    Next shapeName
End Sub

Private Sub SyncCheckboxShape(ByVal ws As Worksheet, ByVal shapeName As String, ByVal isChecked As Boolean)
    If Not ShapeExists(ws, shapeName) Then Exit Sub
    SetShapeText ws.Shapes(shapeName), IIf(isChecked, ChrW$(CHECK_MARK_CODE), "")
End Sub

Private Sub BindResultadoFilterShapes(ByVal ws As Worksheet)
    Dim macroPrefix As String
    Dim shapeName As Variant

    macroPrefix = "'" & ThisWorkbook.Name & "'!"

    SetShapeOnActionIfExists ws, "btnAplicarFiltro", macroPrefix & "AplicarFiltro"
    SetShapeOnActionIfExists ws, "btnLimparFiltro", macroPrefix & "LimparFiltro"

    For Each shapeName In Array( _
        "cbStatus_Aprovado", _
        "cbStatus_MargemQuinze", _
        "cbStatus_Reprovado", _
        "cbStatus_SemMatch", _
        "cbProc_Completo", _
        "cbProc_SoARMPIL", _
        "cbProc_SoSELE", _
        "cbProc_Nenhum", _
        "lblStatus_Aprovado", _
        "lblStatus_MargemQuinze", _
        "lblStatus_Reprovado", _
        "lblStatus_SemMatch", _
        "lblProc_Completo", _
        "lblProc_SoARMPIL", _
        "lblProc_SoSELE", _
        "lblProc_Nenhum")
        SetShapeOnActionIfExists ws, CStr(shapeName), macroPrefix & "ToggleCheckbox"
    Next shapeName
End Sub

Private Function GetResultadoTable(ByVal ws As Worksheet) As ListObject
    On Error Resume Next
    Set GetResultadoTable = ws.ListObjects(RESULTADO_TABLE_NAME)
    On Error GoTo 0

    If GetResultadoTable Is Nothing Then
        If ws.ListObjects.count > 0 Then Set GetResultadoTable = ws.ListObjects(1)
    End If
End Function

Private Function GetResultadoLastDataRow(ByVal ws As Worksheet, ByVal lo As ListObject) As Long
    If Not lo Is Nothing Then
        If Not lo.DataBodyRange Is Nothing Then
            GetResultadoLastDataRow = lo.DataBodyRange.Row + lo.DataBodyRange.Rows.Count - 1
            Exit Function
        End If
    End If

    GetResultadoLastDataRow = GetLastUsedRowInColumns(ws, 2, 10)
End Function

Private Sub ClearResultadoFilters(ByVal ws As Worksheet, ByVal lo As ListObject)
    On Error Resume Next

    If Not lo Is Nothing Then
        If lo.ShowAutoFilter Then
            If lo.AutoFilter.FilterMode Then lo.AutoFilter.ShowAllData
        End If
    End If

    If ws.FilterMode Then ws.ShowAllData

    On Error GoTo 0
End Sub

Private Sub SetFiltroMensagem(ByVal ws As Worksheet, ByVal messageText As String)
    With ws.Range(FILTER_MESSAGE_CELL)
        .Value = messageText
        .Font.Name = "Segoe UI"
        .Font.Size = 18
        .Font.Italic = True
        If Trim$(messageText) = "" Then
            .Font.Color = RGB(156, 87, 0)
        Else
            .Font.Color = RGB(156, 87, 0)
        End If
    End With
End Sub

Private Function ResolveCheckboxStateCell(ByVal ws As Worksheet, ByVal callerName As String, ByRef checkboxShapeName As String) As Range
    Select Case callerName
        Case "cbStatus_Aprovado", "lblStatus_Aprovado"
            checkboxShapeName = "cbStatus_Aprovado"
            Set ResolveCheckboxStateCell = ws.Range("M3")
        Case "cbStatus_MargemQuinze", "lblStatus_MargemQuinze"
            checkboxShapeName = "cbStatus_MargemQuinze"
            Set ResolveCheckboxStateCell = ws.Range("M4")
        Case "cbStatus_Reprovado", "lblStatus_Reprovado"
            checkboxShapeName = "cbStatus_Reprovado"
            Set ResolveCheckboxStateCell = ws.Range("M5")
        Case "cbStatus_SemMatch", "lblStatus_SemMatch"
            checkboxShapeName = "cbStatus_SemMatch"
            Set ResolveCheckboxStateCell = ws.Range("M6")
        Case "cbProc_Completo", "lblProc_Completo"
            checkboxShapeName = "cbProc_Completo"
            Set ResolveCheckboxStateCell = ws.Range("M8")
        Case "cbProc_SoARMPIL", "lblProc_SoARMPIL"
            checkboxShapeName = "cbProc_SoARMPIL"
            Set ResolveCheckboxStateCell = ws.Range("M9")
        Case "cbProc_SoSELE", "lblProc_SoSELE"
            checkboxShapeName = "cbProc_SoSELE"
            Set ResolveCheckboxStateCell = ws.Range("M10")
        Case "cbProc_Nenhum", "lblProc_Nenhum"
            checkboxShapeName = "cbProc_Nenhum"
            Set ResolveCheckboxStateCell = ws.Range("M11")
    End Select
End Function

Private Function GetBooleanCellValue(ByVal target As Range, ByVal defaultValue As Boolean) As Boolean
    Dim rawValue As Variant

    rawValue = target.Value
    If IsError(rawValue) Or IsNull(rawValue) Or IsEmpty(rawValue) Then
        GetBooleanCellValue = defaultValue
        Exit Function
    End If

    Select Case VarType(rawValue)
        Case vbBoolean
            GetBooleanCellValue = CBool(rawValue)
        Case vbString
            Select Case UCase$(Trim$(CStr(rawValue)))
                Case "TRUE", "VERDADEIRO", "1", "SIM"
                    GetBooleanCellValue = True
                Case "FALSE", "FALSO", "0", "NAO", "N"
                    GetBooleanCellValue = False
                Case Else
                    GetBooleanCellValue = defaultValue
            End Select
        Case vbByte, vbInteger, vbLong, vbSingle, vbDouble, vbCurrency, vbDecimal
            GetBooleanCellValue = (CDbl(rawValue) <> 0)
        Case Else
            GetBooleanCellValue = defaultValue
    End Select
End Function

Private Function ShapeExists(ByVal ws As Worksheet, ByVal shapeName As String) As Boolean
    Dim shp As Shape

    On Error Resume Next
    Set shp = ws.Shapes(shapeName)
    ShapeExists = Not shp Is Nothing
    On Error GoTo 0
End Function

Private Sub SetShapeVisibleIfExists(ByVal ws As Worksheet, ByVal shapeName As String, ByVal isVisible As Boolean)
    If Not ShapeExists(ws, shapeName) Then Exit Sub

    On Error Resume Next
    ws.Shapes(shapeName).Visible = isVisible
    On Error GoTo 0
End Sub

Private Sub SetShapeOnActionIfExists(ByVal ws As Worksheet, ByVal shapeName As String, ByVal macroName As String)
    If Not ShapeExists(ws, shapeName) Then Exit Sub

    On Error Resume Next
    ws.Shapes(shapeName).OnAction = macroName
    On Error GoTo 0
End Sub

Private Sub SetShapeText(ByVal shp As Shape, ByVal textValue As String)
    On Error Resume Next
    shp.TextFrame2.TextRange.Text = textValue
    If Err.Number <> 0 Then
        Err.Clear
        shp.TextFrame.Characters.Text = textValue
    End If
    On Error GoTo 0
End Sub
