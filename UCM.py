import os
from pathlib import Path
from colorama import Fore
import shutil
import subprocess
import time
import datetime
import zipfile as zp
from fabric import Connection
from paramiko.ssh_exception import SSHException, NoValidConnectionsError

class MsgType:
    ERROR = Fore.RED
    INFO = Fore.BLUE
    SYSTEM = Fore.YELLOW
    SUCCESS = Fore.GREEN

def is_empty(obj):
    if not isinstance(obj, str):
        raise ValueError(create_output('O Argumento deve ser uma string.', 1))
    return not obj.strip()

def list_files(path, show_hidden=True):
    path = Path(path)
    validate_path(path, True)
    
    arquivos = [f for f in path.iterdir() if show_hidden or not f.name.startswith('.')]

    if not arquivos:
        print(create_output('Não existe arquivos nesse diretório.', 3))
    else:
        for f in arquivos:
            print(create_output(f'{'[D]' if f.is_dir() else '[A]'} {f.name}', 2))
    return arquivos

def show_path():
    try: 
        diretorio = input(create_output('Diretório: ', 3))
        if is_empty(diretorio):
            raise ValueError(create_output('O argumento está vazio.', 1))
        list_files(diretorio)
    except Exception as e:
        print(create_output(f"Um erro inesperado aconteceu {e}", 1))
        return None
    return diretorio

def create_output(msg, tipo):
    tipos = {
        1: MsgType.ERROR,
        2: MsgType.INFO,
        3: MsgType.SYSTEM,
        4: MsgType.SUCCESS
    }
    return f"{tipos.get(tipo, MsgType.ERROR)}{msg}{Fore.RESET}"

def conta_tempo(start):
    duration = time.time() - start
    return create_output(f"Tempo da operação: {duration:.2f} segundos", 3)

def validate_path(path, is_dir=False):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(create_output(f"O caminho {path} não existe.", 1))
    if is_dir and not path.is_dir():
        raise NotADirectoryError(create_output(f"{path} não é um diretório.", 1))
    if not is_dir and not path.is_file():
        raise IsADirectoryError(create_output(f"{path} não é um arquivo.", 1))
    return True

def is_integer(value):
    if isinstance(value, int):
        return True
    if isinstance(value, str):
        return value.lstrip('-+').isdigit()
    return False

class FileOperation:
    def execute(self):
        raise NotImplementedError("Subclasses devem implementar este método!")

class MoveFileOperation(FileOperation):
    def execute(self):
        start = time.time()
        try:
            dir_path = show_path()
            src_path = Path(input(create_output("Arquivo: ", 2)))
            validate_path(Path(dir_path)/src_path)
            dst_path = Path(input(create_output("Para onde: ", 2)))
            validate_path(dst_path, is_dir=True)
            shutil.move(src_path, dst_path)
            print(create_output(f"Arquivo movido para {dst_path}", 4))
        except Exception as e:
            print(create_output(str(e), 1))
        finally:
            print(conta_tempo(start))

class RenameFileOperation(FileOperation):
    def execute(self):
        start = time.time()
        try:
            src_path = Path(input(create_output("Caminho do arquivo: ", 2)))
            new_name = input(create_output("Novo nome: ", 2))
            validate_path(src_path)
            new_path = src_path.with_name(new_name)
            src_path.rename(new_path)
            print(create_output(f"Arquivo renomeado para {new_name} com sucesso", 4))
        except Exception as e:
            print(create_output(str(e), 1))
        finally:
            print(conta_tempo(start))

class CreateFolderOperation(FileOperation):
    def execute(self):
        start = time.time()
        try:
            folder_name = input(create_output("Nome da pasta: ", 2))
            parent_dir = input(create_output("Diretório (deixe em branco para local atual): ", 2)) or "."
            path = Path(parent_dir) / folder_name
            path.mkdir(parents=True, exist_ok=True)
            print(create_output(f"Pasta criada: {path}", 4))
        except Exception as e:
            print(create_output(str(e), 1))
        finally:
            print(conta_tempo(start))

class DeleteFileOrFolderOperation(FileOperation):
    def execute(self):
        start = time.time()
        try:
            is_file = input(create_output("1 - Arquivo, 2 - Pasta: ", 2))
            if not is_integer(is_file):
                print(create_output("Opção deve ser um número inteiro.", 1))
                return
            is_file = int(is_file)
            path = Path(input(create_output("Caminho: ", 2)))
            if is_file == 1:
                validate_path(path)
                path.unlink()
                print(create_output(f"Arquivo {path} removido.", 4))
            elif is_file == 2:
                validate_path(path, is_dir=True)
                shutil.rmtree(path)
                print(create_output(f"Pasta {path} removida.", 4))
            else:
                print(create_output("Opção inválida.", 1))
        except Exception as e:
            print(create_output(str(e), 1))
        finally:
            print(conta_tempo(start))

class CreatePythonExecutableOperation(FileOperation):
    def execute(self):
        start = time.time()
        try:
            output_dir = Path(input(create_output("Diretório de destino: ", 2)))
            script_path = Path(input(create_output("Caminho do script Python: ", 2)))
            validate_path(script_path)
            subprocess.run(["pyinstaller", "--onefile", "--distpath", str(output_dir), str(script_path)], check=True)
            print(create_output(f"Executável criado em {output_dir}", 4))
        except subprocess.CalledProcessError as e:
            print(create_output(f"Erro ao criar executável: {e.stderr}", 1))
        except Exception as e:
            print(create_output(str(e), 1))
        finally:
            print(conta_tempo(start))

#WIP
"""
class RemoveServer(FileOperation):
    def execute(self):
        def make_connection():
            host = input(create_output("Host: "))
            user = input(create_output("Nome de usuario: "))
            pwd = input(create_output("Senha: "))

            try:
                conn = Connection(host=host, user=user, connect_kwargs={"password": pwd})
            except NoValidConnectionsError as e:
                print(create_output(f'Erro de conexão: {e}', 1))
            except SSHException as e:
                print(create_output(f'Erro SSH: {e}', 1))
            except Exception as e:
                print(create_output(f'Um erro inesperado aconteceu: {e}', 1))

        def create_command(command, hide_output, connection):
            try:
                result = connection.run(command, hide_output=hide_output)
                print(create_output(f'Comando "{command}" executado com sucesso: {result.stdout}', 4))
            except Exception as e:
                print(create_output(f'Não foi possível executar o comando "{command}": {e}', 1))
"""
class ExtractOrCompileOperation(FileOperation):
    def execute(self):
        start = time.time()
        try:
            action = input(create_output("1 - Extrair, 2 - Compilar: ", 2))
            if not is_integer(action):
                print(create_output("Opção deve ser um número inteiro.", 1))
                return
            action = int(action)
            if action == 1:
                file_path = Path(input(create_output("Caminho do arquivo ZIP: ", 2)))
                validate_path(file_path)
                destination = Path(input(create_output("Diretório de destino: ", 2)))
                with zp.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(destination)
                print(create_output(f"Arquivos extraídos para {destination}", 4))
            elif action == 2:
                zip_name = input(create_output("Nome do arquivo ZIP: ", 2)) + '.zip'
                with zp.ZipFile(zip_name, 'w') as zip_file:
                    files_to_zip = input(create_output("Arquivos (separados por vírgula): ", 2)).split(',')
                    for file in files_to_zip:
                        file_path = Path(file.strip())
                        validate_path(file_path)
                        zip_file.write(file_path)
                print(create_output(f"Arquivo {zip_name} criado com sucesso.", 4))
            else:
                print(create_output("Opção inválida.", 1))
        except Exception as e:
            print(create_output(str(e), 1))
        finally:
            print(conta_tempo(start))
class ReinstallWindowsOperation(FileOperation):
    def execute(self):
        start = time.time()
        try:
            if os.name != 'nt':
                print(create_output("Operação exclusiva para Windows.", 1))
                return

            print(create_output("\n--- PREPARAÇÃO DE REINSTALAÇÃO (ISO) ---", 3))
            iso_path = Path(input(create_output("Caminho completo da ISO: ", 2)))
            validate_path(iso_path)

            dest_drive = input(create_output("Letra da unidade de destino (ex: D, E): ", 2)).strip().upper()
            if not dest_drive or dest_drive == "C":
                print(create_output("Unidade inválida. Não use a partição do sistema (C:).", 1))
                return

            confirm = input(create_output(f"Isso apagará dados em {dest_drive}: e copiará a ISO. Continuar? (S/N): ", 3)).upper()
            if confirm != 'S': return

            print(create_output("Montando ISO...", 3))
            mount_cmd = f"PowerShell Mount-DiskImage -ImagePath '{iso_path}'"
            subprocess.run(mount_cmd, shell=True, check=True)

            get_letter = f"PowerShell (Get-DiskImage -ImagePath '{iso_path}' | Get-Volume).DriveLetter"
            iso_drive = subprocess.check_output(get_letter, shell=True).decode().strip()

            if not iso_drive:
                print(create_output("Erro ao montar a imagem ISO.", 1))
                return

            print(create_output(f"ISO montada em {iso_drive}:. Copiando arquivos para {dest_drive}:...", 2))

            subprocess.run(["robocopy", f"{iso_drive}:\\", f"{dest_drive}:\\", "/MIR", "/W:0", "/R:0"], check=False)

            print(create_output("Configurando setor de boot...", 3))
            boot_cmd = f"{dest_drive}:\\boot\\bootsect.exe /nt60 {dest_drive}: /force /mbr"
            subprocess.run(boot_cmd, shell=True, check=True)

            subprocess.run(f"PowerShell Dismount-DiskImage -ImagePath '{iso_path}'", shell=True)

            print(create_output(f"\nSucesso! Reinicie o PC e dê boot pela unidade {dest_drive}:", 4))

        except Exception as e:
            print(create_output(f"Erro na preparação: {e}", 1))
        finally:
            print(conta_tempo(start))

class FileManager:
    def __init__(self):
        self.menu()

    def menu(self):
        while True:
            try:
                print(create_output("\nOpções:\n"
                      "1 - Mover arquivo\n"
                      "2 - Renomear arquivo\n"
                      "3 - Criar pasta\n"
                      "4 - Excluir arquivo ou pasta\n"
                      "5 - Criar executável Python\n"
                      "6 - Extrair ou Compilar arquivo\n"
                      "7 - Reinstalar o Windows\n"
                      "0 - Sair", 3))
                choice = input(create_output("Escolha uma opção: ", 2))
                if not is_integer(choice):
                    print(create_output("Opção deve ser um número inteiro.", 1))
                    continue
                choice = int(choice)
                if choice == 0:
                    break
                operations = {
                    1: MoveFileOperation(),
                    2: RenameFileOperation(),
                    3: CreateFolderOperation(),
                    4: DeleteFileOrFolderOperation(),
                    5: CreatePythonExecutableOperation(),
                    6: ExtractOrCompileOperation()
                }
                operation = operations.get(choice)
                if operation:
                    operation.execute()
                else:
                    print(create_output("Opção inválida.", 1))
            except ValueError:
                print(create_output("Por favor, insira um número válido.", 1))
            except Exception as e:
                print(create_output(f"Erro: {e}", 1))

if __name__ == "__main__":
    FileManager()
