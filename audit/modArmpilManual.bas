Option Explicit
Option Private Module

' ================================================================
' modArmpilManual
' ================================================================


Public Function PromptPilarInput(ByVal ws As Worksheet, ByVal preferredPrefix As String) As String
    Dim resp As Variant
    Dim parsedValues() As String
    Dim defaultValue As String

    defaultValue = GetSuggestedNextPilarInput(ws)

    Do
        resp = Application.InputBox( _
            "Informe o numero do pilar ou um intervalo numerico." & vbCrLf & _
            "O prefixo " & preferredPrefix & " sera aplicado automaticamente." & vbCrLf & _
            "Ex.: " & preferredPrefix & IIf(defaultValue <> "", defaultValue, "44") & "  ou  1-5", _
            "Adicionar pilar", _
            defaultValue, _
            Type:=2 _
        )

        If IsDialogCancelled(resp) Then Exit Function

        If TryParsePilarSelection(CStr(resp), preferredPrefix, parsedValues) Then
            PromptPilarInput = Trim$(CStr(resp))
            Exit Function
        End If

        MsgBox "Informe um pilar unico (44 ou 48A) ou um intervalo numerico como 1-5.", vbExclamation, "Adicionar pilar"
    Loop
End Function

Public Function PromptLanceSelectionInput(ByVal ws As Worksheet) As String
    Dim resp As Variant
    Dim parsedValues() As Long
    Dim defaultValue As String

    defaultValue = GetSuggestedLanceForNewPilar(ws)

    Do
        resp = Application.InputBox( _
            "Informe o lance ou um intervalo numerico." & vbCrLf & _
            "Ex.: " & IIf(defaultValue <> "", defaultValue, "3") & "  ou  1-5", _
            "Adicionar pilar", _
            defaultValue, _
            Type:=2 _
        )

        If IsDialogCancelled(resp) Then Exit Function

        If TryParsePositiveLongSelection(CStr(resp), parsedValues) Then
            PromptLanceSelectionInput = Trim$(CStr(resp))
            Exit Function
        End If

        MsgBox "Informe um lance unico ou um intervalo numerico como 1-5.", vbExclamation, "Adicionar pilar"
    Loop
End Function

Public Function PromptPositiveLongValue(ByVal promptText As String, ByVal titleText As String, ByVal defaultValue As String, ByRef parsedValue As Long) As Boolean
    Dim resp As Variant

    Do
        resp = Application.InputBox(promptText, titleText, defaultValue, Type:=2)
        If IsDialogCancelled(resp) Then Exit Function

        If TryGetPositiveLong(CStr(resp), parsedValue) Then
            PromptPositiveLongValue = True
            Exit Function
        End If

        MsgBox "Informe um numero inteiro maior que zero.", vbExclamation, titleText
    Loop
End Function

Public Function PromptPositiveDoubleValue(ByVal promptText As String, ByVal titleText As String, ByVal defaultValue As String, ByRef parsedValue As Double) As Boolean
    Dim resp As Variant

    Do
        resp = Application.InputBox(promptText, titleText, defaultValue, Type:=2)
        If IsDialogCancelled(resp) Then Exit Function

        If TryGetPositiveDouble(CStr(resp), parsedValue) Then
            PromptPositiveDoubleValue = True
            Exit Function
        End If

        MsgBox "Informe um numero maior que zero.", vbExclamation, titleText
    Loop
End Function

Public Function PromptUniformValueChoice(ByVal promptText As String, ByVal titleText As String, ByRef useSameValue As Boolean) As Boolean
    Dim choice As VbMsgBoxResult

    choice = MsgBox(promptText, vbQuestion + vbYesNoCancel, titleText)
    If choice = vbCancel Then Exit Function

    useSameValue = (choice = vbYes)
    PromptUniformValueChoice = True
End Function

Public Function PromptPositiveLongListValues(ByVal promptText As String, ByVal titleText As String, ByVal defaultValue As String, ByVal expectedCount As Long, ByRef parsedValues() As Long) As Boolean
    Dim resp As Variant

    Do
        resp = Application.InputBox(promptText, titleText, defaultValue, Type:=2)
        If IsDialogCancelled(resp) Then Exit Function

        If TryParsePositiveLongList(CStr(resp), expectedCount, parsedValues) Then
            PromptPositiveLongListValues = True
            Exit Function
        End If

        MsgBox "Informe exatamente " & expectedCount & " valores inteiros maiores que zero, separados por ';'.", vbExclamation, titleText
    Loop
End Function

Public Function PromptPositiveDoubleListValues(ByVal promptText As String, ByVal titleText As String, ByVal defaultValue As String, ByVal expectedCount As Long, ByRef parsedValues() As Double) As Boolean
    Dim resp As Variant

    Do
        resp = Application.InputBox(promptText, titleText, defaultValue, Type:=2)
        If IsDialogCancelled(resp) Then Exit Function

        If TryParsePositiveDoubleList(CStr(resp), expectedCount, parsedValues) Then
            PromptPositiveDoubleListValues = True
            Exit Function
        End If

        MsgBox "Informe exatamente " & expectedCount & " valores maiores que zero, separados por ';'.", vbExclamation, titleText
    Loop
End Function

Public Function GetSuggestedNextPilarInput(ByVal ws As Worksheet) As String
    Dim lastRow As Long
    Dim data As Variant
    Dim i As Long
    Dim maxNumber As Long
    Dim currentNumber As Double

    lastRow = GetLastUsedRowInColumns(ws, 2, 2)
    If lastRow < 6 Then Exit Function

    data = ws.Range(ws.Cells(6, 2), ws.Cells(lastRow, 2)).Value2
    If IsArray(data) Then
        For i = 1 To UBound(data, 1)
            currentNumber = GetPilarSortNumber(CStr(data(i, 1)))
            If currentNumber > 0# And currentNumber < 1000000000# Then
                If CLng(currentNumber) > maxNumber Then maxNumber = CLng(currentNumber)
            End If
        Next i
    Else
        currentNumber = GetPilarSortNumber(CStr(data))
        If currentNumber > 0# And currentNumber < 1000000000# Then maxNumber = CLng(currentNumber)
    End If

    If maxNumber > 0 Then GetSuggestedNextPilarInput = CStr(maxNumber + 1)
End Function

Public Function GetSuggestedLanceForNewPilar(ByVal ws As Worksheet) As String
    Dim lastRow As Long
    Dim cellValue As String

    lastRow = GetLastUsedRowInColumns(ws, 3, 3)
    If lastRow < 6 Then Exit Function

    cellValue = Trim$(CStr(ws.Cells(lastRow, 3).Value2))
    If IsNumeric(cellValue) Then GetSuggestedLanceForNewPilar = cellValue
End Function

Public Function GetSuggestedQtyForNewPilar(ByVal ws As Worksheet) As String
    Dim lastRow As Long
    Dim cellValue As String

    lastRow = GetLastUsedRowInColumns(ws, 4, 4)
    If lastRow < 6 Then Exit Function

    cellValue = Trim$(CStr(ws.Cells(lastRow, 4).Value2))
    If IsNumeric(cellValue) Then GetSuggestedQtyForNewPilar = cellValue
End Function

Public Function GetSuggestedBitolaForNewPilar(ByVal ws As Worksheet) As String
    Dim lastRow As Long
    Dim cellValue As String

    lastRow = GetLastUsedRowInColumns(ws, 5, 5)
    If lastRow < 6 Then Exit Function

    cellValue = Trim$(CStr(ws.Cells(lastRow, 5).Value2))
    If IsNumeric(CleanCSV(cellValue)) Then GetSuggestedBitolaForNewPilar = cellValue
End Function

Public Function GetPreferredPilarPrefix(ByVal ws As Worksheet) As String
    Dim detectedPrefix As String

    If TryGetPilarPrefixFromSheet(ws, detectedPrefix) Then
        GetPreferredPilarPrefix = detectedPrefix
        Exit Function
    End If

    On Error Resume Next
    If TryGetPilarPrefixFromSheet(ThisWorkbook.Sheets("SELE"), detectedPrefix) Then
        GetPreferredPilarPrefix = detectedPrefix
    Else
        GetPreferredPilarPrefix = "P"
    End If
    On Error GoTo 0
End Function

Public Function TryGetPilarPrefixFromSheet(ByVal ws As Worksheet, ByRef detectedPrefix As String) As Boolean
    Dim lastRow As Long
    Dim data As Variant
    Dim i As Long
    Dim pilarText As String

    lastRow = GetLastUsedRowInColumns(ws, 2, 2)
    If lastRow < 6 Then Exit Function

    data = ws.Range(ws.Cells(6, 2), ws.Cells(lastRow, 2)).Value2

    If IsArray(data) Then
        For i = 1 To UBound(data, 1)
            pilarText = NormalizePilarName(CStr(data(i, 1)))
            If Left$(pilarText, 3) = "PAF" Then
                detectedPrefix = "PAF"
                TryGetPilarPrefixFromSheet = True
                Exit Function
            End If
            If Left$(pilarText, 1) = "P" Then
                detectedPrefix = "P"
                TryGetPilarPrefixFromSheet = True
                Exit Function
            End If
        Next i
    Else
        pilarText = NormalizePilarName(CStr(data))
        If Left$(pilarText, 3) = "PAF" Then
            detectedPrefix = "PAF"
            TryGetPilarPrefixFromSheet = True
        ElseIf Left$(pilarText, 1) = "P" Then
            detectedPrefix = "P"
            TryGetPilarPrefixFromSheet = True
        End If
    End If
End Function

Public Function TryNormalizeManualPilarInput(ByVal rawValue As Variant, ByVal preferredPrefix As String, ByRef normalizedPilar As String) As Boolean
    Dim rawText As String
    Dim pilarBody As String

    rawText = UCase$(Trim$(CStr(rawValue)))
    rawText = Replace(rawText, " ", "")
    If rawText = "" Then Exit Function

    If Left$(rawText, 3) = "PAF" Then
        pilarBody = Mid$(rawText, 4)
    ElseIf Left$(rawText, 1) = "P" Then
        pilarBody = Mid$(rawText, 2)
    Else
        pilarBody = rawText
    End If

    If Not IsSimplePilarBody(pilarBody) Then Exit Function

    normalizedPilar = preferredPrefix & pilarBody
    TryNormalizeManualPilarInput = True
End Function

Public Function IsSimplePilarBody(ByVal pilarBody As String) As Boolean
    Dim i As Long
    Dim ch As String

    pilarBody = Trim$(pilarBody)
    If pilarBody = "" Then Exit Function
    If Not Mid$(pilarBody, 1, 1) Like "#" Then Exit Function

    For i = 1 To Len(pilarBody)
        ch = Mid$(pilarBody, i, 1)
        If Not (ch Like "[A-Z0-9]") Then Exit Function
    Next i

    IsSimplePilarBody = True
End Function

Public Function TryParsePilarSelection(ByVal rawValue As String, ByVal preferredPrefix As String, ByRef parsedValues() As String) As Boolean
    Dim startValue As Long
    Dim endValue As Long
    Dim i As Long
    Dim normalizedPilar As String
    Dim parts() As String
    Dim startToken As String
    Dim endToken As String

    rawValue = UCase$(Trim$(CStr(rawValue)))
    rawValue = Replace(rawValue, " ", "")
    If rawValue = "" Then Exit Function

    If InStr(1, rawValue, "-", vbTextCompare) > 0 Then
        parts = Split(rawValue, "-")
        If UBound(parts) <> 1 Then Exit Function

        startToken = StripPilarPrefixToken(parts(0))
        endToken = StripPilarPrefixToken(parts(1))
        If Not TryGetPositiveLong(startToken, startValue) Then Exit Function
        If Not TryGetPositiveLong(endToken, endValue) Then Exit Function
        If endValue < startValue Then Exit Function

        ReDim parsedValues(1 To endValue - startValue + 1)
        For i = startValue To endValue
            parsedValues(i - startValue + 1) = preferredPrefix & CStr(i)
        Next i

        TryParsePilarSelection = True
        Exit Function
    End If

    If Not TryNormalizeManualPilarInput(rawValue, preferredPrefix, normalizedPilar) Then Exit Function

    ReDim parsedValues(1 To 1)
    parsedValues(1) = normalizedPilar
    TryParsePilarSelection = True
End Function

Public Function TryParsePositiveLongSelection(ByVal rawValue As String, ByRef parsedValues() As Long) As Boolean
    Dim startValue As Long
    Dim endValue As Long
    Dim singleValue As Long
    Dim i As Long

    rawValue = Trim$(CStr(rawValue))
    If rawValue = "" Then Exit Function

    If TryParsePositiveLongRangeText(rawValue, startValue, endValue) Then
        ReDim parsedValues(1 To endValue - startValue + 1)
        For i = startValue To endValue
            parsedValues(i - startValue + 1) = i
        Next i

        TryParsePositiveLongSelection = True
        Exit Function
    End If

    If Not TryGetPositiveLong(rawValue, singleValue) Then Exit Function

    ReDim parsedValues(1 To 1)
    parsedValues(1) = singleValue
    TryParsePositiveLongSelection = True
End Function

Public Function TryExpandArmpilSelections(ByRef selectedPilares() As String, ByRef selectedLances() As Long, ByRef expandedPilares() As String, ByRef expandedLances() As Long, ByRef infoMessage As String) As Boolean
    Dim pilarCount As Long
    Dim lanceCount As Long
    Dim rowCount As Long
    Dim pilarIndex As Long
    Dim lanceIndex As Long
    Dim i As Long

    pilarCount = GetStringArrayCount(selectedPilares)
    lanceCount = GetLongArrayCount(selectedLances)
    If pilarCount <= 0 Or lanceCount <= 0 Then Exit Function

    rowCount = pilarCount * lanceCount

    ReDim expandedPilares(1 To rowCount)
    ReDim expandedLances(1 To rowCount)

    i = 0
    For pilarIndex = 1 To pilarCount
        For lanceIndex = 1 To lanceCount
            i = i + 1
            expandedPilares(i) = selectedPilares(pilarIndex)
            expandedLances(i) = selectedLances(lanceIndex)
        Next lanceIndex
    Next pilarIndex

    TryExpandArmpilSelections = True
End Function

Public Function StripPilarPrefixToken(ByVal rawText As String) As String
    rawText = UCase$(Trim$(rawText))
    rawText = Replace(rawText, " ", "")

    If Left$(rawText, 3) = "PAF" Then
        StripPilarPrefixToken = Mid$(rawText, 4)
    ElseIf Left$(rawText, 1) = "P" Then
        StripPilarPrefixToken = Mid$(rawText, 2)
    Else
        StripPilarPrefixToken = rawText
    End If
End Function

Public Function TryParsePositiveLongRangeText(ByVal rawText As String, ByRef startValue As Long, ByRef endValue As Long) As Boolean
    Dim parts() As String

    rawText = Replace(Trim$(rawText), " ", "")
    If rawText = "" Then Exit Function
    If InStr(1, rawText, "-", vbTextCompare) <= 0 Then Exit Function

    parts = Split(rawText, "-")
    If UBound(parts) <> 1 Then Exit Function
    If Not TryGetPositiveLong(parts(0), startValue) Then Exit Function
    If Not TryGetPositiveLong(parts(1), endValue) Then Exit Function
    If endValue < startValue Then Exit Function

    TryParsePositiveLongRangeText = True
End Function

Public Function TryParsePositiveLongList(ByVal rawText As String, ByVal expectedCount As Long, ByRef parsedValues() As Long) As Boolean
    Dim parts() As String
    Dim i As Long
    Dim token As String
    Dim parsedValue As Long

    rawText = NormalizeListPromptInput(rawText, True)
    If rawText = "" Then Exit Function

    parts = Split(rawText, ";")
    If UBound(parts) - LBound(parts) + 1 <> expectedCount Then Exit Function

    ReDim parsedValues(1 To expectedCount)
    For i = 0 To UBound(parts)
        token = Trim$(parts(i))
        If Not TryGetPositiveLong(token, parsedValue) Then Exit Function
        parsedValues(i + 1) = parsedValue
    Next i

    TryParsePositiveLongList = True
End Function

Public Function TryParsePositiveDoubleList(ByVal rawText As String, ByVal expectedCount As Long, ByRef parsedValues() As Double) As Boolean
    Dim parts() As String
    Dim i As Long
    Dim token As String
    Dim parsedValue As Double

    rawText = NormalizeListPromptInput(rawText, False)
    If rawText = "" Then Exit Function

    parts = Split(rawText, ";")
    If UBound(parts) - LBound(parts) + 1 <> expectedCount Then Exit Function

    ReDim parsedValues(1 To expectedCount)
    For i = 0 To UBound(parts)
        token = Trim$(parts(i))
        If Not TryGetPositiveDouble(token, parsedValue) Then Exit Function
        parsedValues(i + 1) = parsedValue
    Next i

    TryParsePositiveDoubleList = True
End Function

Public Function NormalizeListPromptInput(ByVal rawText As String, ByVal allowCommaSeparator As Boolean) As String
    rawText = Trim$(rawText)
    rawText = Replace(rawText, vbCrLf, ";")
    rawText = Replace(rawText, vbCr, ";")
    rawText = Replace(rawText, vbLf, ";")
    If allowCommaSeparator Then rawText = Replace(rawText, ",", ";")
    If rawText = "" Then Exit Function
    Do While InStr(rawText, ";;") > 0
        rawText = Replace(rawText, ";;", ";")
    Loop
    If Left$(rawText, 1) = ";" Then rawText = Mid$(rawText, 2)
    If rawText = "" Then Exit Function
    If Right$(rawText, 1) = ";" Then rawText = Left$(rawText, Len(rawText) - 1)

    NormalizeListPromptInput = rawText
End Function

Public Function GetStringArrayCount(ByRef values() As String) As Long
    On Error GoTo EmptyArray
    GetStringArrayCount = UBound(values) - LBound(values) + 1
    Exit Function

EmptyArray:
    GetStringArrayCount = 0
End Function

Public Function GetLongArrayCount(ByRef values() As Long) As Long
    On Error GoTo EmptyArray
    GetLongArrayCount = UBound(values) - LBound(values) + 1
    Exit Function

EmptyArray:
    GetLongArrayCount = 0
End Function

Public Function BuildRepeatedDefaultList(ByVal seedValue As String, ByVal itemCount As Long) As String
    Dim i As Long
    Dim normalizedSeed As String

    normalizedSeed = Trim$(seedValue)
    If normalizedSeed = "" Or itemCount <= 0 Then Exit Function

    For i = 1 To itemCount
        If BuildRepeatedDefaultList <> "" Then BuildRepeatedDefaultList = BuildRepeatedDefaultList & "; "
        BuildRepeatedDefaultList = BuildRepeatedDefaultList & normalizedSeed
    Next i
End Function

Public Function BuildArmpilRowSelectionPreview(ByRef pilarValues() As String, ByRef lanceValues() As Long, ByVal rowCount As Long) As String
    Dim i As Long
    Dim maxItems As Long

    If rowCount <= 0 Then Exit Function

    maxItems = rowCount
    If maxItems > 8 Then maxItems = 8

    For i = 1 To maxItems
        If BuildArmpilRowSelectionPreview <> "" Then BuildArmpilRowSelectionPreview = BuildArmpilRowSelectionPreview & vbCrLf
        BuildArmpilRowSelectionPreview = BuildArmpilRowSelectionPreview & " - " & pilarValues(i) & " / lance " & lanceValues(i)
    Next i

    If rowCount > maxItems Then
        BuildArmpilRowSelectionPreview = BuildArmpilRowSelectionPreview & vbCrLf & " - ..."
    End If
End Function

Public Function NormalizeManualArmpilEntries(ByVal ws As Worksheet, ByRef rowCount As Long, ByRef infoMessage As String) As Boolean
    On Error GoTo TrataErro

    Dim stage As String
    Dim lastRow As Long
    stage = "identificar ultima linha"
    lastRow = GetLastArmpilDataRow(ws)
    If lastRow < 6 Then
        infoMessage = "Nenhuma linha preenchida na ARMPIL para atualizar."
        Exit Function
    End If

    Dim maxRows As Long
    stage = "dimensionar buffers"
    maxRows = lastRow - FIRST_DATA_ROW + 1

    Dim dataOut() As Variant
    ReDim dataOut(1 To maxRows, 1 To 4)

    Dim pilarValues() As String
    Dim hasLance() As Boolean
    Dim lanceValues() As Long
    Dim qtyValues() As Long
    Dim diamValues() As Double
    Dim sourceRows() As Long
    ReDim pilarValues(1 To maxRows)
    ReDim hasLance(1 To maxRows)
    ReDim lanceValues(1 To maxRows)
    ReDim qtyValues(1 To maxRows)
    ReDim diamValues(1 To maxRows)
    ReDim sourceRows(1 To maxRows)

    Dim issueList As String
    Dim issueCount As Long
    Dim i As Long
    Dim pilarText As String
    Dim lanceValue As Long
    Dim qtyValue As Long
    Dim diamValue As Double
    Dim rowDetail As String
    Dim preferredPrefix As String
    Dim lanceText As String
    Dim rawPilar As Variant
    Dim rawLance As Variant
    Dim rawQty As Variant
    Dim rawDiam As Variant

    rowCount = 0
    stage = "identificar prefixo"
    preferredPrefix = GetPreferredPilarPrefix(ws)

    stage = "validar linhas manuais"
    For i = 1 To maxRows
        rawPilar = ws.Cells(FIRST_DATA_ROW + i - 1, COL_PILAR).Value2
        rawLance = ws.Cells(FIRST_DATA_ROW + i - 1, COL_LANCE).Value2
        rawQty = ws.Cells(FIRST_DATA_ROW + i - 1, COL_QTD).Value2
        rawDiam = ws.Cells(FIRST_DATA_ROW + i - 1, COL_BITOLA).Value2

        If IsArmpilInputRowEmpty(rawPilar, rawLance, rawQty, rawDiam) Then
            GoTo NextRow
        End If

        rowDetail = ""
        If Not TryNormalizeManualPilarInput(rawPilar, preferredPrefix, pilarText) Then
            rowDetail = "Pilar invalido"
        ElseIf Not TryGetPositiveLong(rawQty, qtyValue) Then
            rowDetail = "Qtd(Qf) invalida"
        ElseIf Not TryGetPositiveDouble(rawDiam, diamValue) Then
            rowDetail = "Bitola invalida"
        Else
            lanceText = Trim$(CStr(rawLance))
            If lanceText <> "" Then
                If Not TryGetPositiveLong(lanceText, lanceValue) Then
                    rowDetail = "Lance invalido"
                End If
            Else
                lanceValue = 0
            End If
        End If

        If rowDetail <> "" Then
            AppendArmpilValidationIssue issueList, issueCount, FIRST_DATA_ROW + i - 1, rowDetail
            GoTo NextRow
        End If

        rowCount = rowCount + 1
        pilarValues(rowCount) = pilarText
        hasLance(rowCount) = (lanceText <> "")
        lanceValues(rowCount) = lanceValue
        qtyValues(rowCount) = qtyValue
        diamValues(rowCount) = diamValue
        sourceRows(rowCount) = FIRST_DATA_ROW + i - 1
NextRow:
    Next i

    If issueCount > 0 Then
        infoMessage = _
            "Existem linhas manuais incompletas ou invalidas na ARMPIL:" & vbCrLf & _
            issueList & vbCrLf & vbCrLf & _
            "Preencha numero do Pilar, Qtd(Qf) e Bitola(mm)." & vbCrLf & _
            "O lance pode ficar em branco somente quando a macro conseguir inferi-lo pelo contexto."
        Exit Function
    End If

    If rowCount = 0 Then
        infoMessage = "Nenhuma linha valida encontrada na ARMPIL para atualizar."
        Exit Function
    End If

    stage = "resolver lances em branco"
    If Not ResolveMissingManualLances(pilarValues, hasLance, lanceValues, sourceRows, rowCount, infoMessage) Then
        Exit Function
    End If

    stage = "montar saida"
    For i = 1 To rowCount
        dataOut(i, 1) = pilarValues(i)
        dataOut(i, 2) = lanceValues(i)
        dataOut(i, 3) = qtyValues(i)
        dataOut(i, 4) = diamValues(i)
    Next i

    stage = "limpar ARMPIL"
    ClearARMPIL ws
    stage = "renderizar ARMPIL"
    RenderArmpilRows ws, dataOut, rowCount, "  Atualizado manualmente: " & rowCount & " registros"
    stage = "atualizar orientacao"
    SetArmpilManualHint ws

    NormalizeManualArmpilEntries = True
    Exit Function

TrataErro:
    Err.Raise Err.Number, , "NormalizeManualArmpilEntries/" & stage & ": " & Err.Description
End Function

Public Function ResolveMissingManualLances(ByRef pilarValues() As String, ByRef hasLance() As Boolean, ByRef lanceValues() As Long, ByRef sourceRows() As Long, ByVal rowCount As Long, ByRef infoMessage As String) As Boolean
    On Error GoTo TrataErro

    Dim groupStart As Long
    Dim groupEnd As Long

    If rowCount <= 0 Then Exit Function

    groupStart = 1
    Do While groupStart <= rowCount
        groupEnd = groupStart
        Do While groupEnd < rowCount
            If pilarValues(groupEnd + 1) <> pilarValues(groupStart) Then Exit Do
            groupEnd = groupEnd + 1
        Loop

        If Not TryResolveManualLanceGroup(pilarValues, hasLance, lanceValues, sourceRows, rowCount, groupStart, groupEnd, infoMessage) Then
            Exit Function
        End If

        groupStart = groupEnd + 1
    Loop

    ResolveMissingManualLances = True
    Exit Function

TrataErro:
    Err.Raise Err.Number, , "ResolveMissingManualLances/grupo " & groupStart & "-" & groupEnd & ": " & Err.Description
End Function

Public Function TryResolveManualLanceGroup(ByRef pilarValues() As String, ByRef hasLance() As Boolean, ByRef lanceValues() As Long, ByRef sourceRows() As Long, ByVal rowCount As Long, ByVal groupStart As Long, ByVal groupEnd As Long, ByRef infoMessage As String) As Boolean
    On Error GoTo TrataErro

    Dim i As Long
    Dim hasMissing As Boolean
    Dim prevSeq As String
    Dim nextSeq As String
    Dim candidateSeq As String

    For i = groupStart To groupEnd
        If Not hasLance(i) Then
            hasMissing = True
            Exit For
        End If
    Next i

    If Not hasMissing Then
        TryResolveManualLanceGroup = True
        Exit Function
    End If

    prevSeq = GetNeighborExplicitLanceSequence(pilarValues, hasLance, lanceValues, rowCount, groupStart, groupEnd, -1)
    nextSeq = GetNeighborExplicitLanceSequence(pilarValues, hasLance, lanceValues, rowCount, groupStart, groupEnd, 1)
    candidateSeq = ChooseCandidateLanceSequence(prevSeq, nextSeq, hasLance, lanceValues, groupStart, groupEnd)

    If candidateSeq = "" Then
        infoMessage = BuildMissingLanceMessage(pilarValues(groupStart), sourceRows, groupStart, groupEnd)
        Exit Function
    End If

    ApplyCandidateLanceSequence hasLance, lanceValues, groupStart, groupEnd, candidateSeq
    TryResolveManualLanceGroup = True
    Exit Function

TrataErro:
    Err.Raise Err.Number, , "TryResolveManualLanceGroup/" & pilarValues(groupStart) & " linhas " & sourceRows(groupStart) & "-" & sourceRows(groupEnd) & ": " & Err.Description
End Function

Public Function GetNeighborExplicitLanceSequence(ByRef pilarValues() As String, ByRef hasLance() As Boolean, ByRef lanceValues() As Long, ByVal rowCount As Long, ByVal groupStart As Long, ByVal groupEnd As Long, ByVal direction As Long) As String
    Dim idx As Long
    Dim neighborStart As Long
    Dim neighborEnd As Long

    If direction < 0 Then
        idx = groupStart - 1
        Do While idx >= 1
            neighborEnd = idx
            neighborStart = idx
            Do While neighborStart > 1
                If pilarValues(neighborStart - 1) <> pilarValues(neighborEnd) Then Exit Do
                neighborStart = neighborStart - 1
            Loop

            GetNeighborExplicitLanceSequence = BuildExplicitLanceSequence(hasLance, lanceValues, neighborStart, neighborEnd)
            If GetNeighborExplicitLanceSequence <> "" Then Exit Function

            idx = neighborStart - 1
        Loop
    Else
        idx = groupEnd + 1
        Do While idx <= rowCount
            neighborStart = idx
            neighborEnd = idx
            Do While neighborEnd < rowCount
                If pilarValues(neighborEnd + 1) <> pilarValues(neighborStart) Then Exit Do
                neighborEnd = neighborEnd + 1
            Loop

            GetNeighborExplicitLanceSequence = BuildExplicitLanceSequence(hasLance, lanceValues, neighborStart, neighborEnd)
            If GetNeighborExplicitLanceSequence <> "" Then Exit Function

            idx = neighborEnd + 1
        Loop
    End If
End Function

Public Function BuildExplicitLanceSequence(ByRef hasLance() As Boolean, ByRef lanceValues() As Long, ByVal groupStart As Long, ByVal groupEnd As Long) As String
    Dim i As Long

    For i = groupStart To groupEnd
        If Not hasLance(i) Then Exit Function
        If BuildExplicitLanceSequence <> "" Then BuildExplicitLanceSequence = BuildExplicitLanceSequence & ","
        BuildExplicitLanceSequence = BuildExplicitLanceSequence & CStr(lanceValues(i))
    Next i
End Function

Public Function ChooseCandidateLanceSequence(ByVal prevSeq As String, ByVal nextSeq As String, ByRef hasLance() As Boolean, ByRef lanceValues() As Long, ByVal groupStart As Long, ByVal groupEnd As Long) As String
    Dim groupSize As Long
    Dim prevMatches As Boolean
    Dim nextMatches As Boolean
    Dim interSeq As String

    groupSize = groupEnd - groupStart + 1

    If prevSeq <> "" Then
        prevMatches = (CountCsvItems(prevSeq) = groupSize) And DoesCandidateMatchGroup(prevSeq, hasLance, lanceValues, groupStart, groupEnd)
    End If
    If nextSeq <> "" Then
        nextMatches = (CountCsvItems(nextSeq) = groupSize) And DoesCandidateMatchGroup(nextSeq, hasLance, lanceValues, groupStart, groupEnd)
    End If

    If prevMatches And nextMatches Then
        If prevSeq = nextSeq Then
            ChooseCandidateLanceSequence = prevSeq
            Exit Function
        End If
    ElseIf prevMatches Then
        ChooseCandidateLanceSequence = prevSeq
        Exit Function
    ElseIf nextMatches Then
        ChooseCandidateLanceSequence = nextSeq
        Exit Function
    End If

    If prevSeq <> "" And nextSeq <> "" Then
        interSeq = BuildOrderedLanceIntersection(prevSeq, nextSeq)
        If CountCsvItems(interSeq) = groupSize Then
            If DoesCandidateMatchGroup(interSeq, hasLance, lanceValues, groupStart, groupEnd) Then
                ChooseCandidateLanceSequence = interSeq
            End If
        End If
    End If
End Function

Public Function BuildOrderedLanceIntersection(ByVal leftSeq As String, ByVal rightSeq As String) As String
    Dim dict As Object
    Set dict = CreateObject("Scripting.Dictionary")

    Dim seen As Object
    Set seen = CreateObject("Scripting.Dictionary")

    Dim parts() As String
    Dim i As Long
    Dim token As String

    If Trim$(leftSeq) = "" Or Trim$(rightSeq) = "" Then Exit Function

    parts = Split(rightSeq, ",")
    For i = LBound(parts) To UBound(parts)
        token = Trim$(parts(i))
        If token <> "" Then dict(token) = True
    Next i

    parts = Split(leftSeq, ",")
    For i = LBound(parts) To UBound(parts)
        token = Trim$(parts(i))
        If token <> "" Then
            If dict.Exists(token) Then
                If Not seen.Exists(token) Then
                    If BuildOrderedLanceIntersection <> "" Then BuildOrderedLanceIntersection = BuildOrderedLanceIntersection & ","
                    BuildOrderedLanceIntersection = BuildOrderedLanceIntersection & token
                    seen(token) = True
                End If
            End If
        End If
    Next i
End Function

Public Function DoesCandidateMatchGroup(ByVal candidateSeq As String, ByRef hasLance() As Boolean, ByRef lanceValues() As Long, ByVal groupStart As Long, ByVal groupEnd As Long) As Boolean
    Dim i As Long
    Dim token As String

    If Trim$(candidateSeq) = "" Then Exit Function
    If CountCsvItems(candidateSeq) <> (groupEnd - groupStart + 1) Then Exit Function

    For i = groupStart To groupEnd
        token = GetCsvItem(candidateSeq, i - groupStart)
        If Not IsNumeric(token) Then Exit Function
        If hasLance(i) Then
            If CLng(token) <> lanceValues(i) Then Exit Function
        End If
    Next i

    DoesCandidateMatchGroup = True
End Function

Public Sub ApplyCandidateLanceSequence(ByRef hasLance() As Boolean, ByRef lanceValues() As Long, ByVal groupStart As Long, ByVal groupEnd As Long, ByVal candidateSeq As String)
    Dim i As Long
    Dim token As String

    For i = groupStart To groupEnd
        If Not hasLance(i) Then
            token = GetCsvItem(candidateSeq, i - groupStart)
            If Not IsNumeric(token) Then Err.Raise vbObjectError + 2201, , "Sequencia de lances invalida: " & candidateSeq
            lanceValues(i) = CLng(token)
            hasLance(i) = True
        End If
    Next i
End Sub

Public Function GetCsvItem(ByVal csvText As String, ByVal zeroBasedIndex As Long) As String
    Dim parts() As String

    If zeroBasedIndex < 0 Then Exit Function

    parts = Split(csvText, ",")
    If zeroBasedIndex > UBound(parts) Then Exit Function

    GetCsvItem = Trim$(parts(zeroBasedIndex))
End Function

Public Function BuildMissingLanceMessage(ByVal pilarName As String, ByRef sourceRows() As Long, ByVal groupStart As Long, ByVal groupEnd As Long) As String
    Dim firstRow As Long
    Dim lastRow As Long

    firstRow = sourceRows(groupStart)
    lastRow = sourceRows(groupEnd)

    If firstRow = lastRow Then
        BuildMissingLanceMessage = _
            "Nao foi possivel identificar automaticamente o lance do pilar " & pilarName & "." & vbCrLf & _
            "Preencha o lance na linha " & firstRow & " e rode novamente."
    Else
        BuildMissingLanceMessage = _
            "Nao foi possivel identificar automaticamente os lances do pilar " & pilarName & "." & vbCrLf & _
            "Preencha os lances nas linhas " & firstRow & " a " & lastRow & " e rode novamente."
    End If
End Function

Public Function IsArmpilInputRowEmpty(ByVal pilarValue As Variant, ByVal lanceValue As Variant, ByVal qtyValue As Variant, ByVal diamValue As Variant) As Boolean
    IsArmpilInputRowEmpty = _
        Trim$(CStr(pilarValue)) = "" And _
        Trim$(CStr(lanceValue)) = "" And _
        Trim$(CStr(qtyValue)) = "" And _
        Trim$(CStr(diamValue)) = ""
End Function

Public Sub AppendArmpilValidationIssue(ByRef issueList As String, ByRef issueCount As Long, ByVal rowNumber As Long, ByVal detail As String)
    issueCount = issueCount + 1
    If issueCount <= 8 Then
        If issueList <> "" Then issueList = issueList & vbCrLf
        issueList = issueList & " - Linha " & rowNumber & ": " & detail
    ElseIf issueCount = 9 Then
        issueList = issueList & vbCrLf & " - ..."
    End If
End Sub

Public Function TryGetPositiveLong(ByVal cellValue As Variant, ByRef parsedValue As Long) As Boolean
    Dim parsedDouble As Double

    If Not TryGetPositiveDouble(cellValue, parsedDouble) Then Exit Function
    parsedValue = CLng(parsedDouble)
    If parsedDouble <> parsedValue Then Exit Function

    TryGetPositiveLong = (parsedValue > 0)
End Function

Public Function TryGetPositiveDouble(ByVal cellValue As Variant, ByRef parsedValue As Double) As Boolean
    Dim rawText As String

    rawText = CleanCSV(CStr(cellValue))
    If rawText = "" Then Exit Function

    parsedValue = Val(rawText)
    If parsedValue <= 0# Then Exit Function

    TryGetPositiveDouble = True
End Function
