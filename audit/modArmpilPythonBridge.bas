Option Explicit
Option Private Module

' ================================================================
' modArmpilPythonBridge
' ================================================================


Public Function RunPythonArmpilExtractor() As String
    Dim oldStatusBar As Variant
    Dim errNum As Long
    Dim errDesc As String
    Dim pdfPath As String
    Dim levelsCsv As String
    Dim allLevelsCsv As String
    Dim lanceMap As String
    Dim stage As String

    oldStatusBar = Application.StatusBar
    Application.StatusBar = "Executando extrator ARMPIL..."

    On Error GoTo Cleanup

    stage = "selecionar PDF"
    pdfPath = PickArmpilPdfPath()
    If pdfPath = "" Then GoTo Cleanup

    Dim scriptPath As String
    stage = "localizar script Python"
    scriptPath = GetArmpilScriptPath()
    If scriptPath = "" Then GoTo Cleanup

    Dim pythonExe As String
    Dim pythonArgs As String
    stage = "localizar interpretador Python"
    If Not GetPythonCommand(pythonExe, pythonArgs) Then
        Err.Raise vbObjectError + 2000, , "Python não encontrado. Instale o Python ou ajuste o launcher no VBA."
    End If

    stage = "ler niveis do PDF"
    levelsCsv = GetArmpilLevels(pythonExe, pythonArgs, scriptPath, pdfPath, allLevelsCsv)

    If levelsCsv <> "" Then
        stage = "mapear lances"
        lanceMap = ResolveArmpilLanceMap(levelsCsv, allLevelsCsv)
        If lanceMap = "" Then GoTo Cleanup
    ElseIf allLevelsCsv <> "" Then
        MsgBox BuildArmpilLevelsPrompt(allLevelsCsv, levelsCsv) & vbCrLf & vbCrLf & _
            "Nenhum lance/nivel com armadura longitudinal foi identificado para mapear.", _
            vbInformation, _
            "Mapear lances ARMPIL"
    End If

    Dim shellObj As Object
    Dim exitCode As Long
    Dim resultFile As String
    Dim launcherFile As String
    Dim resultText As String

    resultFile = Environ$("TEMP") & Application.PathSeparator & "armpil_result_" & Format$(Now, "yyyymmdd_hhnnss") & ".txt"
    launcherFile = Environ$("TEMP") & Application.PathSeparator & "armpil_run_" & Format$(Now, "yyyymmdd_hhnnss") & ".cmd"

    stage = "executar extrator Python"
    WriteTextFile launcherFile, BuildPythonLauncherScript(pythonExe, pythonArgs, scriptPath, resultFile, pdfPath, lanceMap)

    Set shellObj = CreateObject("WScript.Shell")
    exitCode = shellObj.Run("cmd.exe /d /c " & QuotePath(launcherFile), 0, True)

    stage = "ler retorno do extrator"
    resultText = ReadTextFileSafe(resultFile)
    If Dir$(resultFile) <> "" Then Kill resultFile
    If Dir$(launcherFile) <> "" Then Kill launcherFile

    If exitCode <> 0 Then
        If InStr(1, resultText, "[CANCELADO]", vbTextCompare) > 0 Then
            GoTo Cleanup
        End If

        Err.Raise vbObjectError + 2001, , BuildPythonErrorMessage(resultText, launcherFile)
    End If

    RunPythonArmpilExtractor = ExtractTaggedValue(resultText, "CSV_OUTPUT=")
    If RunPythonArmpilExtractor = "" Then
        Err.Raise vbObjectError + 2002, , "O script Python terminou sem informar o CSV gerado."
    End If

    If Not FileExists(RunPythonArmpilExtractor) Then
        Err.Raise vbObjectError + 2003, , "CSV gerado não encontrado:" & vbCrLf & RunPythonArmpilExtractor
    End If

Cleanup:
    errNum = Err.Number
    errDesc = Err.Description
    Application.StatusBar = oldStatusBar
    If errNum <> 0 Then
        If stage <> "" Then
            Err.Raise errNum, , "Etapa '" & stage & "': " & errDesc
        Else
            Err.Raise errNum, , errDesc
        End If
    End If
End Function

Public Function GetArmpilLevels(ByVal pythonExe As String, ByVal pythonArgs As String, ByVal scriptPath As String, ByVal pdfPath As String, ByRef allLevelsCsv As String) As String
    Dim shellObj As Object
    Dim exitCode As Long
    Dim resultFile As String
    Dim launcherFile As String
    Dim resultText As String

    resultFile = Environ$("TEMP") & Application.PathSeparator & "armpil_levels_" & Format$(Now, "yyyymmdd_hhnnss") & ".txt"
    launcherFile = Environ$("TEMP") & Application.PathSeparator & "armpil_levels_" & Format$(Now, "yyyymmdd_hhnnss") & ".cmd"

    WriteTextFile launcherFile, BuildPythonLauncherScript(pythonExe, pythonArgs, scriptPath, resultFile, pdfPath, "", "--levels")

    Set shellObj = CreateObject("WScript.Shell")
    exitCode = shellObj.Run("cmd.exe /d /c " & QuotePath(launcherFile), 0, True)

    resultText = ReadTextFileSafe(resultFile)
    If Dir$(resultFile) <> "" Then Kill resultFile
    If Dir$(launcherFile) <> "" Then Kill launcherFile

    If exitCode <> 0 Then
        Err.Raise vbObjectError + 2006, , BuildPythonErrorMessage(resultText, launcherFile)
    End If

    GetArmpilLevels = ExtractTaggedValue(resultText, "LEVELS=")
    allLevelsCsv = ExtractTaggedValue(resultText, "ALL_LEVELS=")
    If allLevelsCsv = "" Then allLevelsCsv = GetArmpilLevels
End Function

Public Function PickArmpilPdfPath() As String
    PickArmpilPdfPath = PickFilePath("Selecione o PDF ARMPIL", "PDF", "*.pdf")
End Function

Public Function GetArmpilScriptPath() As String
    Dim sep As String
    sep = Application.PathSeparator

    Dim candidates(2) As String
    candidates(0) = ThisWorkbook.Path & sep & "armpil_extractor.py"
    candidates(1) = ThisWorkbook.Path & sep & ".." & sep & "src" & sep & "armpil_extractor.py"
    candidates(2) = ThisWorkbook.Path & sep & "src" & sep & "armpil_extractor.py"

    Dim i As Long
    For i = 0 To UBound(candidates)
        If Dir$(candidates(i)) <> "" Then
            GetArmpilScriptPath = candidates(i)
            Exit Function
        End If
    Next i

    Err.Raise vbObjectError + 2004, , _
        "Arquivo armpil_extractor.py não encontrado." & vbCrLf & _
        "Locais verificados:" & vbCrLf & _
        candidates(0) & vbCrLf & _
        candidates(1) & vbCrLf & _
        candidates(2)
End Function

Public Function GetPythonCommand(ByRef exeName As String, ByRef exeArgs As String) As Boolean
    Dim candidates As Variant
    Dim candidate As Variant

    candidates = Array( _
        Array("python", ""), _
        Array("py", "-3"), _
        Array("python3", "") _
    )

    For Each candidate In candidates
        If CanRunPythonInterpreter(CStr(candidate(0)), Trim$(CStr(candidate(1)))) Then
            exeName = CStr(candidate(0))
            exeArgs = Trim$(CStr(candidate(1)))
            GetPythonCommand = True
            Exit Function
        End If
    Next candidate
End Function

Public Function CanRunPythonInterpreter(ByVal exeName As String, ByVal exeArgs As String) As Boolean
    Dim shellObj As Object
    Dim launcherFile As String
    Dim exitCode As Long

    Set shellObj = CreateObject("WScript.Shell")
    launcherFile = Environ$("TEMP") & Application.PathSeparator & "armpil_check_" & Replace(exeName, ".", "_") & ".cmd"

    WriteTextFile launcherFile, BuildPythonCheckScript(exeName, exeArgs)
    exitCode = shellObj.Run("cmd.exe /d /c " & QuotePath(launcherFile), 0, True)
    If Dir$(launcherFile) <> "" Then Kill launcherFile

    CanRunPythonInterpreter = (exitCode = 0)
End Function

Public Function QuotePath(ByVal path As String) As String
    QuotePath = Chr$(34) & path & Chr$(34)
End Function

Public Function BuildExecutableCommand(ByVal exeName As String, ByVal args As String) As String
    Dim cmd As String

    cmd = QuotePath(exeName)
    If Trim$(args) <> "" Then
        cmd = cmd & " " & Trim$(args)
    End If

    BuildExecutableCommand = cmd
End Function

Public Function BuildPythonLauncherScript(ByVal exeName As String, ByVal exeArgs As String, ByVal scriptPath As String, ByVal resultFile As String, ByVal pdfPath As String, Optional ByVal lanceMap As String = "", Optional ByVal extraArgs As String = "") As String
    Dim lines As String

    lines = "@echo off" & vbCrLf
    lines = lines & "setlocal" & vbCrLf
    lines = lines & "set ""ARMPIL_RESULT_FILE=" & resultFile & """" & vbCrLf
    lines = lines & "set ""ARMPIL_OUTPUT_DIR=" & GetArmpilOutputDir() & """" & vbCrLf
    lines = lines & "set ""ARMPIL_PDF_PATH=" & pdfPath & """" & vbCrLf
    lines = lines & "set ""ARMPIL_KNOWN_LANCES=" & GetKnownLancesForPython() & """" & vbCrLf
    If Trim$(lanceMap) <> "" Then
        lines = lines & "set ""ARMPIL_LANCE_MAP=" & lanceMap & """" & vbCrLf
    End If
    lines = lines & BuildExecutableCommand(exeName, exeArgs) & " " & QuotePath(scriptPath)
    If Trim$(extraArgs) <> "" Then
        lines = lines & " " & Trim$(extraArgs)
    End If
    lines = lines & vbCrLf
    lines = lines & "exit /b %errorlevel%" & vbCrLf

    BuildPythonLauncherScript = lines
End Function

Public Function BuildPythonCheckScript(ByVal exeName As String, ByVal exeArgs As String) As String
    Dim lines As String

    lines = "@echo off" & vbCrLf
    lines = lines & BuildExecutableCommand(exeName, exeArgs) & " -c ""import sys, fitz; exit(0 if getattr(sys, '_is_gil_enabled', lambda: True)() else 1)""" & vbCrLf
    lines = lines & "exit /b %errorlevel%" & vbCrLf

    BuildPythonCheckScript = lines
End Function

Public Function GetArmpilOutputDir() As String
    Dim publicDir As String
    publicDir = Environ$("PUBLIC")

    If publicDir <> "" Then
        GetArmpilOutputDir = publicDir & Application.PathSeparator & "Documents" & _
            Application.PathSeparator & "Scripts Formula" & Application.PathSeparator & "ARMPIL"
    Else
        GetArmpilOutputDir = Environ$("TEMP")
    End If
End Function

Public Function ExtractTaggedValue(ByVal text As String, ByVal tag As String) As String
    Dim normalized As String
    Dim lines() As String
    Dim i As Long
    Dim line As String

    normalized = Replace(text, vbCrLf, vbLf)
    normalized = Replace(normalized, vbCr, vbLf)
    lines = Split(normalized, vbLf)

    For i = LBound(lines) To UBound(lines)
        line = Trim$(lines(i))
        If Left$(line, Len(tag)) = tag Then
            ExtractTaggedValue = Trim$(Mid$(line, Len(tag) + 1))
            Exit Function
        End If
    Next i
End Function

Public Function BuildPythonErrorMessage(ByVal stdoutText As String, ByVal stderrText As String) As String
    Dim msg As String

    msg = Trim$(stdoutText)
    If msg = "" Then msg = "Falha ao executar o script Python." & vbCrLf & vbCrLf & "Comando:" & vbCrLf & stderrText

    BuildPythonErrorMessage = msg
End Function

Public Function ReadTextFileSafe(ByVal path As String) As String
    Dim ff As Integer

    If Dir$(path) = "" Then Exit Function

    ff = FreeFile
    Open path For Input As #ff
    ReadTextFileSafe = Input$(LOF(ff), #ff)
    Close #ff
End Function

Public Function FileExists(ByVal path As String) As Boolean
    On Error GoTo Fallback
    FileExists = CreateObject("Scripting.FileSystemObject").FileExists(path)
    Exit Function

Fallback:
    FileExists = (Dir$(path) <> "")
End Function

Public Sub WriteTextFile(ByVal path As String, ByVal content As String)
    Dim ff As Integer

    ff = FreeFile
    Open path For Output As #ff
    Print #ff, content;
    Close #ff
End Sub
