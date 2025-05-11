/**
 * VESA - メインJavaScriptファイル
 */

document.addEventListener('DOMContentLoaded', () => {
    // ドキュメント削除の確認
    const deleteForm = document.getElementById('deleteForm');
    if (deleteForm) {
        deleteForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const documentId = e.target.getAttribute('data-document-id');
            if (!documentId) return;
            
            try {
                const response = await fetch(`/api/documents/${documentId}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    window.location.href = '/';
                } else {
                    const data = await response.json();
                    showAlert('danger', `エラー: ${data.detail || '削除に失敗しました'}`);
                }
            } catch (error) {
                showAlert('danger', `エラー: ${error.message}`);
            }
        });
    }
    
    // アラートメッセージの表示
    function showAlert(type, message) {
        const alertContainer = document.createElement('div');
        alertContainer.className = `alert alert-${type} alert-dismissible fade show`;
        alertContainer.setAttribute('role', 'alert');
        
        alertContainer.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        const container = document.querySelector('.container');
        container.insertBefore(alertContainer, container.firstChild);
        
        // 5秒後に自動的に消える
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alertContainer);
            bsAlert.close();
        }, 5000);
    }
    
    // Markdownプレビュー
    const previewButtons = document.querySelectorAll('.preview-button');
    for (const button of previewButtons) {
        button.addEventListener('click', (e) => {
            const contentId = e.target.getAttribute('data-content-id');
            const content = document.getElementById(contentId).value;
            const previewId = e.target.getAttribute('data-preview-id');
            const previewElement = document.getElementById(previewId);
            
            // Markdownをレンダリング（簡易的な実装）
            fetch('/api/markdown/render', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content })
            })
            .then(response => response.json())
            .then(data => {
                previewElement.innerHTML = data.html;
            })
            .catch(error => {
                console.error('Error rendering markdown:', error);
                previewElement.innerHTML = '<div class="alert alert-danger">プレビューの生成に失敗しました。</div>';
            });
        });
    }
    
    // タグの自動補完
    const tagInput = document.getElementById('tags');
    if (tagInput) {
        // サーバーからタグ一覧を取得する関数
        async function fetchTags() {
            try {
                const response = await fetch('/api/tags');
                if (response.ok) {
                    const data = await response.json();
                    return data.tags || [];
                }
                return [];
            } catch (error) {
                console.error('Error fetching tags:', error);
                return [];
            }
        }
        
        // タグ入力欄にフォーカスが当たったときにタグ一覧を取得
        tagInput.addEventListener('focus', async (e) => {
            if (!e.target.dataset.tagsLoaded) {
                const tags = await fetchTags();
                e.target.dataset.tagsLoaded = 'true';
                e.target.dataset.tags = JSON.stringify(tags);
            }
        });
        
        // タグ入力時の処理
        tagInput.addEventListener('input', () => {
            // ここに自動補完のロジックを実装
            // 簡易的な実装のため省略
        });
    }
    
    // ドキュメント関連付け
    const relateButton = document.getElementById('relate-document');
    if (relateButton) {
        relateButton.addEventListener('click', (e) => {
            const sourceId = e.target.getAttribute('data-source-id');
            const targetId = document.getElementById('target-document').value;
            const relationType = document.getElementById('relationship-type').value;
            
            if (!sourceId || !targetId || !relationType) {
                showAlert('warning', '関連付けに必要な情報が不足しています。');
                return;
            }
            
            fetch('/api/documents/relationships/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    source_id: sourceId,
                    target_id: targetId,
                    relationship_type: relationType
                })
            })
            .then(response => {
                if (response.ok) {
                    showAlert('success', 'ドキュメントを関連付けました。');
                    // モーダルを閉じる
                    const modal = bootstrap.Modal.getInstance(document.getElementById('relateModal'));
                    if (modal) modal.hide();
                    // ページをリロード
                    window.location.reload();
                } else {
                    return response.json().then(data => {
                        throw new Error(data.detail || '関連付けに失敗しました。');
                    });
                }
            })
            .catch(error => {
                showAlert('danger', `エラー: ${error.message}`);
            });
        });
    }
});
