def test_list_files_success(authorized_client, test_file):
    response = authorized_client.get("/files/")
    print(response.json())
    assert response.status_code == 200
    assert "files" in response.json()
    assert len(response.json()["files"]) > 0

def test_generate_source_file_link(authorized_client,test_file):
    res = authorized_client.get(f'files/{test_file.id}/generate-secure-link')
    generated_url = res.json()
    print(f"GEnerated Url : {generated_url}")
    assert res.status_code ==200
    assert generated_url['message']=="success"

def test_unauthorized_generate_source_file_link(authorized_ops,test_file):
    res = authorized_ops.get(f'files/{test_file.id}/generate-secure-link')
    generated_url = res.json()
    print(generated_url)
    assert res.status_code ==500
    assert generated_url['detail']=='Failed to generate secure link: 403: Only Client users can generate secure links'

def test_download_file_success(authorized_client, test_secure_link):
    response = authorized_client.get(
        f"/files/download/{test_secure_link['download_link'].split('/')[-1]}",
    )
    assert response.status_code == 200
    assert response.headers.get("content-disposition") is not None
    assert "attachment; filename=" in response.headers.get("content-disposition")

def test_download_file_invalid_token(authorized_client):
    response = authorized_client.get("/files/download/invalid_token")
    print(response.json())
    assert response.status_code == 500
    assert "Invalid or expired secure link" in response.json().get("detail")

