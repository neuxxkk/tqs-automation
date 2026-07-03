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
    Dim preparedPdfPath As String
    Dim tempPdfPath As String
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

    stage = "preparar caminho do PDF"
    preparedPdfPath = PrepareArmpilPdfPathForPython(pdfPath, tempPdfPath)
    If preparedPdfPath = "" Then GoTo Cleanup

    Dim scriptPath As String
    stage = "localizar script Python"
    scriptPath = ResolveArmpilScriptPath()
    If scriptPath = "" Then GoTo Cleanup

    Dim pythonExe As String
    Dim pythonArgs As String
    stage = "localizar interpretador Python"
    If Not GetPythonCommand(pythonExe, pythonArgs) Then
        Err.Raise vbObjectError + 2000, , "Python não encontrado. Instale o Python ou ajuste o launcher no VBA."
    End If

    stage = "ler niveis do PDF"
    levelsCsv = GetArmpilLevels(pythonExe, pythonArgs, scriptPath, preparedPdfPath, allLevelsCsv)

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
    WriteTextFile launcherFile, BuildPythonLauncherScript(pythonExe, pythonArgs, scriptPath, resultFile, preparedPdfPath, lanceMap)

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

    SaveStoredArmpilLanceLevelMap lanceMap

    If Not FileExists(RunPythonArmpilExtractor) Then
        Err.Raise vbObjectError + 2003, , "CSV gerado não encontrado:" & vbCrLf & RunPythonArmpilExtractor
    End If

Cleanup:
    errNum = Err.Number
    errDesc = Err.Description
    DeleteFileIfExists tempPdfPath
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

Public Function ResolveArmpilScriptPath() As String
    Dim fso As Object
    Dim sep As String
    Dim basePath As String
    Dim candidate As String
    Dim checkedPaths As String
    Dim depth As Long

    Set fso = CreateObject("Scripting.FileSystemObject")
    sep = Application.PathSeparator
    basePath = ThisWorkbook.Path

    For depth = 0 To 6
        candidate = BuildChildPath(basePath, "src" & sep & "armpil_extractor.py")
        If Dir$(candidate) <> "" Then
            ResolveArmpilScriptPath = candidate
            Exit Function
        End If
        checkedPaths = AppendCheckedPath(checkedPaths, candidate)

        candidate = BuildChildPath(basePath, "armpil_extractor.py")
        If Dir$(candidate) <> "" Then
            ResolveArmpilScriptPath = candidate
            Exit Function
        End If
        checkedPaths = AppendCheckedPath(checkedPaths, candidate)

        If depth = 6 Then Exit For
        If Not fso.FolderExists(basePath) Then Exit For
        If StrComp(basePath, fso.GetParentFolderName(basePath), vbTextCompare) = 0 Then Exit For
        basePath = fso.GetParentFolderName(basePath)
        If Trim$(basePath) = "" Then Exit For
    Next depth

    Err.Raise vbObjectError + 2004, , _
        "Arquivo armpil_extractor.py nao encontrado." & vbCrLf & _
        "Locais verificados:" & vbCrLf & _
        checkedPaths
End Function

Public Function BuildChildPath(ByVal basePath As String, ByVal relativePath As String) As String
    If Right$(basePath, 1) = Application.PathSeparator Then
        BuildChildPath = basePath & relativePath
    Else
        BuildChildPath = basePath & Application.PathSeparator & relativePath
    End If
End Function

Public Function AppendCheckedPath(ByVal existingText As String, ByVal pathText As String) As String
    If existingText = "" Then
        AppendCheckedPath = pathText
    ElseIf InStr(1, existingText, pathText, vbTextCompare) > 0 Then
        AppendCheckedPath = existingText
    Else
        AppendCheckedPath = existingText & vbCrLf & pathText
    End If
End Function

Public Function PickArmpilPdfPath() As String
    PickArmpilPdfPath = PickFilePath("Selecione o PDF ARMPIL", "PDF", "*.pdf")
End Function

Public Function PrepareArmpilPdfPathForPython(ByVal pdfPath As String, ByRef tempPdfPath As String) As String
    Dim resolvedPath As String

    resolvedPath = Trim$(pdfPath)
    If resolvedPath = "" Then Exit Function

    resolvedPath = ResolveMappedDrivePath(resolvedPath)

    If IsRemotePdfPath(resolvedPath) Then
        tempPdfPath = CopyPdfToLocalTemp(resolvedPath)
        PrepareArmpilPdfPathForPython = tempPdfPath
    Else
        PrepareArmpilPdfPathForPython = resolvedPath
    End If
End Function

Public Function ResolveMappedDrivePath(ByVal filePath As String) As String
    Dim normalized As String
    Dim driveRoot As String
    Dim remoteRoot As String
    Dim relativePart As String

    normalized = Trim$(filePath)
    If normalized = "" Then Exit Function

    If Left$(normalized, 2) = "\\" Then
        ResolveMappedDrivePath = normalized
        Exit Function
    End If

    If Len(normalized) < 3 Then
        ResolveMappedDrivePath = normalized
        Exit Function
    End If

    If Mid$(normalized, 2, 2) <> ":\" Then
        ResolveMappedDrivePath = normalized
        Exit Function
    End If

    driveRoot = UCase$(Left$(normalized, 2))
    remoteRoot = GetMappedDriveRemoteRoot(driveRoot)

    If remoteRoot = "" Then
        ResolveMappedDrivePath = normalized
        Exit Function
    End If

    relativePart = Mid$(normalized, 3)
    Do While Left$(relativePart, 1) = "\"
        relativePart = Mid$(relativePart, 2)
    Loop

    If Right$(remoteRoot, 1) = "\" Then
        ResolveMappedDrivePath = remoteRoot & relativePart
    ElseIf relativePart <> "" Then
        ResolveMappedDrivePath = remoteRoot & "\" & relativePart
    Else
        ResolveMappedDrivePath = remoteRoot
    End If
End Function

Public Function GetMappedDriveRemoteRoot(ByVal driveRoot As String) As String
    Dim networkObj As Object
    Dim drives As Object
    Dim i As Long
    Dim localName As String

    On Error GoTo Fallback

    Set networkObj = CreateObject("WScript.Network")
    Set drives = networkObj.EnumNetworkDrives

    For i = 0 To drives.Count - 1 Step 2
        localName = UCase$(Trim$(CStr(drives.Item(i))))
        If localName = UCase$(Trim$(driveRoot)) Then
            GetMappedDriveRemoteRoot = Trim$(CStr(drives.Item(i + 1)))
            Exit Function
        End If
    Next i
    Exit Function

Fallback:
    GetMappedDriveRemoteRoot = ""
End Function

Public Function IsRemotePdfPath(ByVal filePath As String) As Boolean
    Dim normalized As String
    Dim fso As Object
    Dim driveName As String

    normalized = Trim$(filePath)
    If normalized = "" Then Exit Function

    If Left$(normalized, 2) = "\\" Then
        IsRemotePdfPath = True
        Exit Function
    End If

    On Error GoTo Fallback
    Set fso = CreateObject("Scripting.FileSystemObject")
    driveName = fso.GetDriveName(normalized)
    If driveName <> "" Then
        IsRemotePdfPath = (fso.GetDrive(driveName).DriveType = 3)
    End If
    Exit Function

Fallback:
    IsRemotePdfPath = False
End Function

Public Function CopyPdfToLocalTemp(ByVal sourcePath As String) As String
    Dim fso As Object
    Dim sourceFile As Object
    Dim tempFolder As String
    Dim targetPath As String
    Dim fileName As String
    Dim baseName As String
    Dim extension As String

    Set fso = CreateObject("Scripting.FileSystemObject")
    If Not fso.FileExists(sourcePath) Then
        Err.Raise vbObjectError + 2010, , "Arquivo PDF nao encontrado:" & vbCrLf & sourcePath
    End If

    tempFolder = Environ$("TEMP") & Application.PathSeparator & "ScriptsFormula" & Application.PathSeparator & "ARMPIL"
    EnsureFolderExists tempFolder

    Set sourceFile = fso.GetFile(sourcePath)
    fileName = sourceFile.Name
    baseName = fso.GetBaseName(fileName)
    extension = fso.GetExtensionName(fileName)

    targetPath = tempFolder & Application.PathSeparator & _
        baseName & "_" & Format$(Now, "yyyymmdd_hhnnss") & "_" & Format$(CLng(Timer * 1000), "00000000") & _
        IIf(extension <> "", "." & extension, "")

    fso.CopyFile sourcePath, targetPath, True
    CopyPdfToLocalTemp = targetPath
End Function

Public Sub EnsureFolderExists(ByVal folderPath As String)
    Dim fso As Object
    Dim parentPath As String

    Set fso = CreateObject("Scripting.FileSystemObject")
    If Trim$(folderPath) = "" Then Exit Sub
    If fso.FolderExists(folderPath) Then Exit Sub

    parentPath = fso.GetParentFolderName(folderPath)
    If parentPath <> "" And Not fso.FolderExists(parentPath) Then
        EnsureFolderExists parentPath
    End If

    If Not fso.FolderExists(folderPath) Then fso.CreateFolder folderPath
End Sub

Public Sub DeleteFileIfExists(ByVal filePath As String)
    If Trim$(filePath) = "" Then Exit Sub

    On Error Resume Next
    If Dir$(filePath) <> "" Then Kill filePath
    On Error GoTo 0
End Sub

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
    lines = lines & "set ""ARMPIL_PDF_PATH=" & pdfPath & """" & vbCrLf
    lines = lines & "set ""ARMPIL_KNOWN_LANCES=" & GetKnownLancesForPython() & """" & vbCrLf
    lines = lines & "set ""ARMPIL_KNOWN_PILAR_LANCES=" & GetKnownPilarLancesForPython() & """" & vbCrLf
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
