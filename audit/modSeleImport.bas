Option Explicit
Option Private Module

' ================================================================
' modSeleImport
' ================================================================


Public Sub LoadSele(ByVal path As String)
    Dim state As AppState

    BeginExcelBatch state

    On Error GoTo Cleanup

    Dim lines As Variant
    lines = ReadAllNonEmptyLines(path)
    If Not IsArray(lines) Then GoTo Cleanup
    If UBound(lines) < LBound(lines) Then GoTo Cleanup

    Dim lancesDict As Object
    Dim lanceTitles As Object
    Set lancesDict = CreateObject("Scripting.Dictionary")
    Set lanceTitles = CreateObject("Scripting.Dictionary")

    Dim currentPilar As String: currentPilar = ""
    Dim i As Long, lanceNum As Long
    Dim asVal As Variant
    Dim lanceTitle As String

    For i = LBound(lines) To UBound(lines)
        Dim line As String: line = Trim$(lines(i))
        If line = "" Then GoTo P1Next

        If Left$(line, 6) = "PILAR:" Then
            currentPilar = ExtractSelePilarName(line)
            GoTo P1Next
        End If

        If currentPilar = "" Then GoTo P1Next
        If Not IsDataLine(line) Then GoTo P1Next
        If Not ParseSeleLine(line, lanceNum, asVal) Then GoTo P1Next

        If Not lancesDict.Exists(lanceNum) Then lancesDict(lanceNum) = True
        If Not lanceTitles.Exists(lanceNum) Then
            lanceTitle = ExtractSeleLanceTitle(line)
            If lanceTitle <> "" Then lanceTitles(lanceNum) = lanceTitle
        End If
P1Next:
    Next i

    If lancesDict.count = 0 Then GoTo Cleanup

    Dim keys As Variant: keys = lancesDict.keys
    SortNumericVariantArray keys

    Dim lanceList As String
    lanceList = JoinVariantList(keys)

    Dim suggestedList As String
    suggestedList = BuildSuggestedSeleLances(keys)

    Dim lanceTitleList As String
    Dim suggestedTitleList As String
    Dim lancePromptList As String
    Dim suggestedPromptList As String
    lanceTitleList = BuildLanceTitleList(keys, lanceTitles)
    suggestedTitleList = BuildLanceTitleListFromCsv(suggestedList, lanceTitles)
    lancePromptList = BuildPromptLanceList(keys, lanceTitles)
    suggestedPromptList = BuildPromptLanceListFromCsv(suggestedList, lanceTitles)

    Dim resp As Variant
    resp = PromptSeleLanceFilter(lanceList, suggestedList, lancePromptList, suggestedPromptList)
    If IsDialogCancelled(resp) Then GoTo Cleanup

    Dim filterSet As Object
    Set filterSet = BuildLanceFilterSet(Trim$(CStr(resp)))

    Dim filterActive As Boolean
    filterActive = (filterSet.count > 0) And (filterSet.count < lancesDict.count)

    Dim maxRows As Long: maxRows = UBound(lines) - LBound(lines) + 1

    Dim arrPilar() As String:   ReDim arrPilar(1 To maxRows)
    Dim arrLance() As Long:     ReDim arrLance(1 To maxRows)
    Dim arrAs()    As Variant:  ReDim arrAs(1 To maxRows)

    Dim rowCount As Long:  rowCount = 0
    currentPilar = ""

    For i = LBound(lines) To UBound(lines)
        line = Trim$(lines(i))
        If line = "" Then GoTo P2Next

        If Left$(line, 6) = "PILAR:" Then
            currentPilar = ExtractSelePilarName(line)
            GoTo P2Next
        End If

        If currentPilar = "" Then GoTo P2Next
        If Not IsDataLine(line) Then GoTo P2Next
        If Not ParseSeleLine(line, lanceNum, asVal) Then GoTo P2Next

        If filterActive Then
            If Not filterSet.Exists(lanceNum) Then GoTo P2Next
        End If

        rowCount = rowCount + 1
        arrPilar(rowCount) = NormalizePilarName(currentPilar)
        arrLance(rowCount) = lanceNum
        If IsNumeric(asVal) Then
            arrAs(rowCount) = CDbl(asVal) / 10#
        Else
            arrAs(rowCount) = CStr(asVal)
        End If
P2Next:
    Next i

    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets("SELE")
    Call ClearSELE(ws)

    If rowCount = 0 Then
        ws.Cells(4, 2).value = "  Nenhum registro para os níveis selecionados."
        GoTo Cleanup
    End If

    ' Monta arrays 2-D para escrita em bloco (uma chamada por coluna)
    Dim colB() As Variant: ReDim colB(1 To rowCount, 1 To 1)
    Dim colC() As Variant: ReDim colC(1 To rowCount, 1 To 1)
    Dim colD() As Variant: ReDim colD(1 To rowCount, 1 To 1)
    Dim colE() As Variant: ReDim colE(1 To rowCount, 1 To 1)

    For i = 1 To rowCount
        colB(i, 1) = arrPilar(i)
        colC(i, 1) = arrLance(i)
        colD(i, 1) = arrAs(i)
        colE(i, 1) = BuildPilarKey(arrPilar(i), arrLance(i))
    Next i

    Dim startRow As Long: startRow = 6
    Dim endRow   As Long: endRow = startRow + rowCount - 1

    With ws
        .Range(.Cells(startRow, 2), .Cells(endRow, 2)).value = colB
        .Range(.Cells(startRow, 3), .Cells(endRow, 3)).value = colC
        .Range(.Cells(startRow, 4), .Cells(endRow, 4)).value = colD
        .Range(.Cells(startRow, 4), .Cells(endRow, 4)).NumberFormat = "0.00"
        .Range(.Cells(startRow, 5), .Cells(endRow, 5)).value = colE
    End With

    SortSheetRangeByPilarLance ws, startRow, endRow, 2, 5, 2, 3, 6
    ApplySeleFormatting ws, startRow, endRow

    ws.Cells(4, 2).value = "  Carregado: " & rowCount & " registros  |  Lances: " & CompactPromptText(lanceTitleList, 160) & "  |  " & path

Cleanup:
    RestoreExcelBatch state
    If Err.Number <> 0 Then
        MsgBox "Erro em LoadSele: " & Err.Description, vbExclamation
    End If
End Sub

Public Function ExtractSelePilarName(ByVal line As String) As String
    Dim raw As String
    Dim sp As Long
    Dim par As Long

    raw = Trim$(Mid$(line, 7))
    sp = InStr(raw, " ")
    If sp > 0 Then raw = Left$(raw, sp - 1)
    par = InStr(raw, "(")
    If par > 0 Then raw = Left$(raw, par - 1)

    ExtractSelePilarName = NormalizePilarName(raw)
End Function

Public Function ExtractSeleLanceTitle(ByVal line As String) As String
    Dim s As String
    Dim rest As String
    Dim sp As Long
    Dim i As Long

    s = LTrim$(line)
    sp = InStr(s, " ")
    If sp = 0 Then Exit Function

    rest = LTrim$(Mid$(s, sp + 1))
    For i = 1 To Len(rest) - 1
        If Mid$(rest, i, 2) = "  " Then
            ExtractSeleLanceTitle = Trim$(Left$(rest, i - 1))
            Exit Function
        End If
    Next i

    ExtractSeleLanceTitle = Trim$(Left$(rest, 16))
End Function

Public Function BuildLanceTitleList(ByVal values As Variant, ByVal titles As Object) As String
    Dim i As Long
    Dim lanceValue As Long
    Dim itemText As String

    If Not IsArray(values) Then Exit Function

    For i = LBound(values) To UBound(values)
        lanceValue = CLng(values(i))
        itemText = CStr(lanceValue)
        If Not titles Is Nothing Then
            If titles.Exists(lanceValue) Then itemText = itemText & ":" & CStr(titles(lanceValue))
        End If

        If BuildLanceTitleList <> "" Then BuildLanceTitleList = BuildLanceTitleList & "; "
        BuildLanceTitleList = BuildLanceTitleList & itemText
    Next i
End Function

Public Function BuildLanceTitleListFromCsv(ByVal lanceCsv As String, ByVal titles As Object) As String
    Dim parts() As String
    Dim i As Long
    Dim token As String
    Dim itemText As String
    Dim lanceValue As Long

    lanceCsv = Replace(lanceCsv, ";", ",")
    If Trim$(lanceCsv) = "" Then Exit Function

    parts = Split(lanceCsv, ",")
    For i = LBound(parts) To UBound(parts)
        token = Trim$(parts(i))
        If token = "" Then GoTo NextItem
        If Not IsNumeric(token) Then GoTo NextItem

        lanceValue = CLng(token)
        itemText = CStr(lanceValue)
        If Not titles Is Nothing Then
            If titles.Exists(lanceValue) Then itemText = itemText & ":" & CStr(titles(lanceValue))
        End If

        If BuildLanceTitleListFromCsv <> "" Then BuildLanceTitleListFromCsv = BuildLanceTitleListFromCsv & "; "
        BuildLanceTitleListFromCsv = BuildLanceTitleListFromCsv & itemText
NextItem:
    Next i
End Function

Public Function BuildPromptLanceList(ByVal values As Variant, ByVal titles As Object) As String
    Dim i As Long
    Dim lanceValue As Long

    If Not IsArray(values) Then Exit Function

    For i = LBound(values) To UBound(values)
        lanceValue = CLng(values(i))
        If BuildPromptLanceList <> "" Then BuildPromptLanceList = BuildPromptLanceList & vbCrLf
        BuildPromptLanceList = BuildPromptLanceList & BuildPromptLanceItem(lanceValue, titles)
    Next i
End Function

Public Function BuildPromptLanceListFromCsv(ByVal lanceCsv As String, ByVal titles As Object) As String
    Dim parts() As String
    Dim i As Long
    Dim token As String

    lanceCsv = Replace(lanceCsv, ";", ",")
    If Trim$(lanceCsv) = "" Then Exit Function

    parts = Split(lanceCsv, ",")
    For i = LBound(parts) To UBound(parts)
        token = Trim$(parts(i))
        If token = "" Then GoTo NextPromptItem
        If Not IsNumeric(token) Then GoTo NextPromptItem

        If BuildPromptLanceListFromCsv <> "" Then BuildPromptLanceListFromCsv = BuildPromptLanceListFromCsv & vbCrLf
        BuildPromptLanceListFromCsv = BuildPromptLanceListFromCsv & BuildPromptLanceItem(CLng(token), titles)
NextPromptItem:
    Next i
End Function

Public Function BuildPromptLanceItem(ByVal lanceValue As Long, ByVal titles As Object) As String
    BuildPromptLanceItem = "[LANCE " & CStr(lanceValue) & "]"
    If Not titles Is Nothing Then
        If titles.Exists(lanceValue) Then BuildPromptLanceItem = BuildPromptLanceItem & "  " & CStr(titles(lanceValue))
    End If
End Function

Public Function BuildSuggestedSeleLances(ByVal availableLances As Variant) As String
    Dim dict As Object
    Set dict = GetSheetLancesDict(ThisWorkbook.Sheets("ARMPIL"), 6, 3)
    If dict.count = 0 Then Exit Function

    Dim matches As Object
    Set matches = CreateObject("Scripting.Dictionary")

    Dim i As Long
    For i = LBound(availableLances) To UBound(availableLances)
        If dict.Exists(CLng(availableLances(i))) Then
            matches(CLng(availableLances(i))) = True
        End If
    Next i

    If matches.count = 0 Then Exit Function

    Dim keys As Variant
    keys = matches.keys
    SortNumericVariantArray keys
    BuildSuggestedSeleLances = JoinVariantList(keys)
End Function

Public Function BuildLanceFilterSet(ByVal rawText As String) As Object
    Dim dict As Object
    Set dict = CreateObject("Scripting.Dictionary")

    Dim cleaned As String
    cleaned = Trim$(rawText)
    If cleaned = "" Then
        Set BuildLanceFilterSet = dict
        Exit Function
    End If

    cleaned = Replace(cleaned, ";", ",")
    cleaned = Replace(cleaned, vbCrLf, ",")
    cleaned = Replace(cleaned, vbCr, ",")
    cleaned = Replace(cleaned, vbLf, ",")

    Dim parts() As String
    parts = Split(cleaned, ",")

    Dim i As Long
    For i = 0 To UBound(parts)
        Dim token As String
        token = Trim$(parts(i))
        If IsNumeric(token) Then
            dict(CLng(token)) = True
        End If
    Next i

    Set BuildLanceFilterSet = dict
End Function

Public Function PromptSeleLanceFilter(ByVal availableList As String, ByVal suggestedList As String, Optional ByVal availableDetails As String = "", Optional ByVal suggestedDetails As String = "") As Variant
    Dim choice As VbMsgBoxResult
    Dim availableDisplay As String
    Dim suggestedDisplay As String

    availableDisplay = Trim$(availableDetails)
    If availableDisplay = "" Then availableDisplay = availableList
    suggestedDisplay = Trim$(suggestedDetails)
    If suggestedDisplay = "" Then suggestedDisplay = suggestedList

    If Trim$(suggestedList) = "" Then
        PromptSeleLanceFilter = ""
        Exit Function
    End If

    If suggestedList <> "" And suggestedList <> availableList Then
        choice = MsgBox( _
            "Lances encontrados no SELE:" & vbCrLf & _
            availableDisplay & vbCrLf & vbCrLf & _
            "Lances que ja existem no ARMPIL carregado:" & vbCrLf & _
            suggestedDisplay & vbCrLf & vbCrLf & _
            "Sim = usar a sugestao do ARMPIL" & vbCrLf & _
            "Nao = escolher manualmente" & vbCrLf & _
            "Cancelar = importar todos os lances", _
            vbQuestion + vbYesNoCancel, _
            "Selecionar niveis" _
        )

        If choice = vbYes Then
            PromptSeleLanceFilter = suggestedList
            Exit Function
        End If

        If choice = vbCancel Then
            PromptSeleLanceFilter = ""
            Exit Function
        End If
    End If

    Dim dlgMsg As String
    Dim resp As Variant
    Dim filterSet As Object

    dlgMsg = "Lances detectados no arquivo:" & vbCrLf & _
             availableDisplay & vbCrLf & vbCrLf & _
             "Informe os lances a importar (separados por virgula)." & vbCrLf & _
             "Deixe em branco para importar todos."

    Do
        resp = Application.InputBox(dlgMsg, "Selecionar Niveis", IIf(suggestedList <> "", suggestedList, availableList), Type:=2)
        If IsDialogCancelled(resp) Then
            PromptSeleLanceFilter = False
            Exit Function
        End If

        Set filterSet = BuildLanceFilterSet(Trim$(CStr(resp)))
        If Trim$(CStr(resp)) = "" Or filterSet.count > 0 Then
            PromptSeleLanceFilter = Trim$(CStr(resp))
            Exit Function
        End If

        MsgBox "Nenhum lance valido foi informado. Tente novamente.", vbExclamation
    Loop
End Function

Public Function IsDataLine(ByVal line As String) As Boolean
    Dim s As String
    s = LTrim$(line)

    If Len(s) = 0 Then
        IsDataLine = False
        Exit Function
    End If

    Dim first As String
    first = Left$(s, InStr(s & " ", " ") - 1)
    IsDataLine = IsNumeric(first)
End Function

Public Function ParseSeleLine(ByVal line As String, ByRef lance As Long, ByRef asVal As Variant) As Boolean
    ParseSeleLine = False

    Dim s As String
    s = line

    Do While InStr(s, "  ") > 0
        s = Replace(s, "  ", " ")
    Loop

    s = Trim$(s)

    Dim parts() As String
    parts = Split(s, " ")

    If UBound(parts) < 2 Then Exit Function
    If Not IsNumeric(parts(0)) Then Exit Function

    lance = CLng(parts(0))

    If InStr(1, s, "AVISO", vbTextCompare) > 0 Then
        asVal = GetNaoDimensionadoText()
        ParseSeleLine = True
        Exit Function
    End If

    If UBound(parts) < 8 Then Exit Function

    Dim i As Long
    For i = 4 To UBound(parts) - 2
        Dim p1 As String, p2 As String
        p1 = UCase$(Trim$(parts(i)))
        p2 = UCase$(Trim$(parts(i + 1)))

        If (p1 = "N" Or p1 = "S") And (p2 = "N" Or p2 = "S") Then
            If i + 2 <= UBound(parts) Then
                If IsNumeric(parts(i + 2)) Then
                    asVal = CDbl(parts(i + 2))
                    ParseSeleLine = True
                    Exit Function
                End If
            End If
        End If
    Next i
End Function
