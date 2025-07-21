// 全域變數
let currentUser = null;
let currentTheme = 'light';

// DOM 載入完成後初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// 初始化應用程式
function initializeApp() {
    // 檢查主題設定
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
    
    // 檢查登入狀態
    checkAuthStatus();
    
    // 綁定事件監聽器
    bindEventListeners();
}

// 綁定事件監聽器
function bindEventListeners() {
    // 登入表單
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // 註冊表單
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
    
    // 主題切換
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // 模態框關閉
    const modal = document.getElementById('modal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModal();
            }
        });
    }
}

// 主題切換
function toggleTheme() {
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
}

function setTheme(theme) {
    currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    const themeIcon = document.querySelector('#theme-toggle i');
    if (themeIcon) {
        themeIcon.className = theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
    }
}

// 檢查認證狀態
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/profile');
        if (response.ok) {
            const user = await response.json();
            currentUser = user;
            showDashboard();
        } else {
            showLoginPage();
        }
    } catch (error) {
        console.error('檢查認證狀態失敗:', error);
        showLoginPage();
    }
}

// 顯示登入頁面
function showLoginPage() {
    hideAllPages();
    document.getElementById('login-page').style.display = 'flex';
    document.getElementById('navbar').style.display = 'none';
}

// 顯示註冊頁面
function showRegisterPage() {
    hideAllPages();
    document.getElementById('register-page').style.display = 'flex';
    document.getElementById('navbar').style.display = 'none';
}

// 顯示儀表板
function showDashboard() {
    hideAllPages();
    document.getElementById('dashboard-page').style.display = 'block';
    document.getElementById('navbar').style.display = 'block';
    
    // 更新導航欄用戶資訊
    updateNavbarUser();
    
    // 根據用戶角色顯示對應的儀表板
    showRoleDashboard();
    
    // 載入初始數據
    loadDashboardData();
}

// 隱藏所有頁面
function hideAllPages() {
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => page.style.display = 'none');
}

// 更新導航欄用戶資訊
function updateNavbarUser() {
    if (currentUser) {
        document.getElementById('nav-user').style.display = 'flex';
        document.getElementById('user-name').textContent = currentUser.full_name;
        document.getElementById('user-role').textContent = getRoleDisplayName(currentUser.role);
        document.getElementById('dashboard-user-name').textContent = currentUser.full_name;
    }
}

// 獲取角色顯示名稱
function getRoleDisplayName(role) {
    const roleNames = {
        'student': '學生',
        'teacher': '老師',
        'admin': '管理員'
    };
    return roleNames[role] || role;
}

// 顯示對應角色的儀表板
function showRoleDashboard() {
    // 隱藏所有儀表板
    document.getElementById('student-dashboard').style.display = 'none';
    document.getElementById('teacher-dashboard').style.display = 'none';
    document.getElementById('admin-dashboard').style.display = 'none';
    
    // 顯示對應角色的儀表板
    if (currentUser) {
        document.getElementById(`${currentUser.role}-dashboard`).style.display = 'block';
    }
}

// 處理登入
async function handleLogin(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const loginData = {
        username: formData.get('username'),
        password: formData.get('password')
    };
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(loginData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            currentUser = result.user;
            showNotification('登入成功', '歡迎回來！', 'success');
            showDashboard();
        } else {
            showNotification('登入失敗', result.error || '請檢查用戶名和密碼', 'error');
        }
    } catch (error) {
        console.error('登入錯誤:', error);
        showNotification('登入失敗', '網路連線錯誤，請稍後再試', 'error');
    }
}

// 處理註冊
async function handleRegister(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const registerData = {
        username: formData.get('username'),
        email: formData.get('email'),
        full_name: formData.get('full_name'),
        role: formData.get('role'),
        password: formData.get('password')
    };
    
    // 如果是學生，添加學號
    if (registerData.role === 'student') {
        registerData.student_id = formData.get('student_id');
    }
    
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(registerData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('註冊成功', '請使用新帳號登入', 'success');
            showLoginPage();
            // 清空註冊表單
            e.target.reset();
        } else {
            showNotification('註冊失敗', result.error || '註冊過程中發生錯誤', 'error');
        }
    } catch (error) {
        console.error('註冊錯誤:', error);
        showNotification('註冊失敗', '網路連線錯誤，請稍後再試', 'error');
    }
}

// 登出
async function logout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
        currentUser = null;
        showNotification('登出成功', '已安全登出', 'info');
        showLoginPage();
    } catch (error) {
        console.error('登出錯誤:', error);
        showNotification('登出失敗', '登出過程中發生錯誤', 'error');
    }
}

// 切換學號欄位顯示
function toggleStudentId() {
    const role = document.getElementById('reg-role').value;
    const studentIdGroup = document.getElementById('student-id-group');
    const studentIdInput = document.getElementById('reg-student-id');
    
    if (role === 'student') {
        studentIdGroup.style.display = 'block';
        studentIdInput.required = true;
    } else {
        studentIdGroup.style.display = 'none';
        studentIdInput.required = false;
        studentIdInput.value = '';
    }
}

// 載入儀表板數據
async function loadDashboardData() {
    if (!currentUser) return;
    
    try {
        switch (currentUser.role) {
            case 'student':
                await loadStudentData();
                break;
            case 'teacher':
                await loadTeacherData();
                break;
            case 'admin':
                await loadAdminData();
                break;
        }
    } catch (error) {
        console.error('載入儀表板數據失敗:', error);
        showNotification('載入失敗', '無法載入儀表板數據', 'error');
    }
}

// 載入學生數據
async function loadStudentData() {
    // 載入課程列表
    await loadStudentCourses();
    // 載入待填寫表單
    await loadPendingForms();
    // 載入出席統計
    await loadStudentAttendanceChart();
}

// 載入學生課程
async function loadStudentCourses() {
    try {
        const response = await fetch('/api/courses');
        if (response.ok) {
            const courses = await response.json();
            displayStudentCourses(courses);
        }
    } catch (error) {
        console.error('載入課程失敗:', error);
    }
}

// 顯示學生課程
function displayStudentCourses(courses) {
    const container = document.getElementById('student-courses');
    
    if (courses.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-book-open"></i>
                <h3>尚未加入任何課程</h3>
                <p>請使用課程代碼加入課程</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = courses.map(course => `
        <div class="course-item">
            <div class="course-title">${course.course_name}</div>
            <div class="course-code">課程代碼: ${course.course_code}</div>
            <div class="course-code">老師: ${course.teacher_name || '未知'}</div>
            <div class="course-actions">
                <button class="btn btn-outline" onclick="viewCourseDetails(${course.id})">
                    <i class="fas fa-eye"></i> 查看詳情
                </button>
                <button class="btn btn-error" onclick="leaveCourse(${course.id})">
                    <i class="fas fa-sign-out-alt"></i> 退出課程
                </button>
            </div>
        </div>
    `).join('');
}

// 載入待填寫表單
async function loadPendingForms() {
    try {
        const response = await fetch('/api/forms');
        if (response.ok) {
            const forms = await response.json();
            const pendingForms = forms.filter(form => !form.submitted);
            displayPendingForms(pendingForms);
        }
    } catch (error) {
        console.error('載入表單失敗:', error);
    }
}

// 顯示待填寫表單
function displayPendingForms(forms) {
    const container = document.getElementById('pending-forms');
    
    if (forms.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-clipboard-check"></i>
                <h3>沒有待填寫的表單</h3>
                <p>所有表單都已完成</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = forms.map(form => `
        <div class="form-item">
            <div class="form-title">${form.title}</div>
            <div class="form-date">日期: ${form.form_date}</div>
            <div class="form-date">時間: ${form.start_time} - ${form.end_time}</div>
            <div class="form-date">課程: ${form.course_name}</div>
            <div class="form-actions">
                <button class="btn btn-primary" onclick="fillAttendanceForm(${form.id})">
                    <i class="fas fa-edit"></i> 填寫出缺席
                </button>
            </div>
        </div>
    `).join('');
}

// 加入課程
async function joinCourse() {
    const joinCode = document.getElementById('join-code').value.trim().toUpperCase();
    
    if (!joinCode) {
        showNotification('錯誤', '請輸入課程代碼', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/courses/join', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ join_code: joinCode })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('成功', result.message, 'success');
            document.getElementById('join-code').value = '';
            await loadStudentCourses();
            await loadPendingForms();
        } else {
            showNotification('失敗', result.error, 'error');
        }
    } catch (error) {
        console.error('加入課程失敗:', error);
        showNotification('錯誤', '網路連線錯誤', 'error');
    }
}

// 退出課程
async function leaveCourse(courseId) {
    if (!confirm('確定要退出這個課程嗎？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/courses/${courseId}/leave`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('成功', result.message, 'success');
            await loadStudentCourses();
            await loadPendingForms();
        } else {
            showNotification('失敗', result.error, 'error');
        }
    } catch (error) {
        console.error('退出課程失敗:', error);
        showNotification('錯誤', '網路連線錯誤', 'error');
    }
}

// 填寫出缺席表單
function fillAttendanceForm(formId) {
    showModal('填寫出缺席', `
        <form id="attendance-form" onsubmit="submitAttendance(event, ${formId})">
            <div class="form-group">
                <label>出缺席狀態</label>
                <div class="input-group">
                    <i class="fas fa-check-circle"></i>
                    <select name="status" required>
                        <option value="">請選擇狀態</option>
                        <option value="present">出席</option>
                        <option value="absent">缺席</option>
                        <option value="late">遲到</option>
                        <option value="excused">請假</option>
                    </select>
                </div>
            </div>
            <div class="form-group">
                <label>備註 (選填)</label>
                <div class="input-group">
                    <i class="fas fa-comment"></i>
                    <input type="text" name="notes" placeholder="如請假原因等">
                </div>
            </div>
            <button type="submit" class="btn btn-primary btn-full">
                <i class="fas fa-save"></i> 提交
            </button>
        </form>
    `);
}

// 提交出缺席
async function submitAttendance(e, formId) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const attendanceData = {
        status: formData.get('status'),
        notes: formData.get('notes') || ''
    };
    
    try {
        const response = await fetch(`/api/forms/${formId}/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(attendanceData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('成功', '出缺席記錄已提交', 'success');
            closeModal();
            await loadPendingForms();
        } else {
            showNotification('失敗', result.error, 'error');
        }
    } catch (error) {
        console.error('提交出缺席失敗:', error);
        showNotification('錯誤', '網路連線錯誤', 'error');
    }
}

// 載入老師數據
async function loadTeacherData() {
    await loadTeacherCourses();
    await loadTeacherAttendanceChart();
}

// 載入老師課程
async function loadTeacherCourses() {
    try {
        const response = await fetch('/api/courses');
        if (response.ok) {
            const courses = await response.json();
            displayTeacherCourses(courses);
        }
    } catch (error) {
        console.error('載入課程失敗:', error);
    }
}

// 顯示老師課程
function displayTeacherCourses(courses) {
    const container = document.getElementById('teacher-courses');
    
    if (courses.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-chalkboard-teacher"></i>
                <h3>尚未建立任何課程</h3>
                <p>點擊上方按鈕建立第一個課程</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = courses.map(course => `
        <div class="course-item">
            <div class="course-title">${course.course_name}</div>
            <div class="course-code">課程代碼: ${course.course_code}</div>
            <div class="course-code">加入代碼: <strong>${course.join_code}</strong></div>
            <div class="course-code">學生人數: ${course.student_count || 0} 人</div>
            <div class="course-actions">
                <button class="btn btn-primary" onclick="viewCourseStudents(${course.id})">
                    <i class="fas fa-users"></i> 學生名單
                </button>
                <button class="btn btn-outline" onclick="editCourse(${course.id})">
                    <i class="fas fa-edit"></i> 編輯
                </button>
            </div>
        </div>
    `).join('');
}

// 顯示建立課程模態框
function showCreateCourseModal() {
    showModal('建立新課程', `
        <form id="create-course-form" onsubmit="createCourse(event)">
            <div class="form-group">
                <label for="course-code">課程代碼</label>
                <div class="input-group">
                    <i class="fas fa-code"></i>
                    <input type="text" id="course-code" name="course_code" required>
                </div>
            </div>
            <div class="form-group">
                <label for="course-name">課程名稱</label>
                <div class="input-group">
                    <i class="fas fa-book"></i>
                    <input type="text" id="course-name" name="course_name" required>
                </div>
            </div>
            <div class="form-group">
                <label for="course-description">課程描述</label>
                <div class="input-group">
                    <i class="fas fa-align-left"></i>
                    <input type="text" id="course-description" name="description" placeholder="選填">
                </div>
            </div>
            <button type="submit" class="btn btn-primary btn-full">
                <i class="fas fa-plus"></i> 建立課程
            </button>
        </form>
    `);
}

// 建立課程
async function createCourse(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const courseData = {
        course_code: formData.get('course_code'),
        course_name: formData.get('course_name'),
        description: formData.get('description') || ''
    };
    
    try {
        const response = await fetch('/api/courses', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(courseData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('成功', '課程建立成功', 'success');
            closeModal();
            await loadTeacherCourses();
        } else {
            showNotification('失敗', result.error, 'error');
        }
    } catch (error) {
        console.error('建立課程失敗:', error);
        showNotification('錯誤', '網路連線錯誤', 'error');
    }
}

// 顯示建立表單模態框
function showCreateFormModal() {
    // 先載入課程列表
    loadCoursesForForm();
}

// 載入課程列表用於表單建立
async function loadCoursesForForm() {
    try {
        const response = await fetch('/api/courses');
        if (response.ok) {
            const courses = await response.json();
            const courseOptions = courses.map(course => 
                `<option value="${course.id}">${course.course_name} (${course.course_code})</option>`
            ).join('');
            
            showModal('建立出缺席表單', `
                <form id="create-form-form" onsubmit="createAttendanceForm(event)">
                    <div class="form-group">
                        <label for="form-title">表單標題</label>
                        <div class="input-group">
                            <i class="fas fa-heading"></i>
                            <input type="text" id="form-title" name="title" required>
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="form-course">選擇課程</label>
                        <div class="input-group">
                            <i class="fas fa-book"></i>
                            <select id="form-course" name="course_id" required>
                                <option value="">請選擇課程</option>
                                ${courseOptions}
                            </select>
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="form-date">日期</label>
                        <div class="input-group">
                            <i class="fas fa-calendar"></i>
                            <input type="date" id="form-date" name="form_date" required>
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="form-start-time">開始時間</label>
                        <div class="input-group">
                            <i class="fas fa-clock"></i>
                            <input type="time" id="form-start-time" name="start_time" required>
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="form-end-time">結束時間</label>
                        <div class="input-group">
                            <i class="fas fa-clock"></i>
                            <input type="time" id="form-end-time" name="end_time" required>
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="form-description">描述</label>
                        <div class="input-group">
                            <i class="fas fa-align-left"></i>
                            <input type="text" id="form-description" name="description" placeholder="選填">
                        </div>
                    </div>
                    <button type="submit" class="btn btn-primary btn-full">
                        <i class="fas fa-plus"></i> 建立表單
                    </button>
                </form>
            `);
        }
    } catch (error) {
        console.error('載入課程失敗:', error);
        showNotification('錯誤', '無法載入課程列表', 'error');
    }
}

// 建立出缺席表單
async function createAttendanceForm(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const attendanceFormData = {
        title: formData.get('title'),
        course_id: parseInt(formData.get('course_id')),
        form_date: formData.get('form_date'),
        start_time: formData.get('start_time'),
        end_time: formData.get('end_time'),
        description: formData.get('description') || ''
    };
    
    try {
        const response = await fetch('/api/forms', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(attendanceFormData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('成功', '出缺席表單建立成功', 'success');
            closeModal();
        } else {
            showNotification('失敗', result.error, 'error');
        }
    } catch (error) {
        console.error('建立表單失敗:', error);
        showNotification('錯誤', '網路連線錯誤', 'error');
    }
}

// 載入管理員數據
async function loadAdminData() {
    await loadAdminOverviewChart();
}

// 載入圖表數據
async function loadStudentAttendanceChart() {
    try {
        const response = await fetch(`/api/analytics/student/${currentUser.id}`);
        if (response.ok) {
            const data = await response.json();
            renderStudentChart(data);
        }
    } catch (error) {
        console.error('載入學生統計失敗:', error);
    }
}

async function loadTeacherAttendanceChart() {
    // 載入老師的課程統計圖表
    try {
        const coursesResponse = await fetch('/api/courses');
        if (coursesResponse.ok) {
            const courses = await coursesResponse.json();
            if (courses.length > 0) {
                const response = await fetch(`/api/analytics/course/${courses[0].id}`);
                if (response.ok) {
                    const data = await response.json();
                    renderTeacherChart(data);
                }
            }
        }
    } catch (error) {
        console.error('載入老師統計失敗:', error);
    }
}

async function loadAdminOverviewChart() {
    try {
        const response = await fetch('/api/analytics/overview');
        if (response.ok) {
            const data = await response.json();
            renderAdminChart(data);
        }
    } catch (error) {
        console.error('載入管理員統計失敗:', error);
    }
}

// 渲染圖表
function renderStudentChart(data) {
    const ctx = document.getElementById('student-attendance-chart');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['出席', '缺席', '遲到', '請假'],
            datasets: [{
                data: [
                    data.status_count.present || 0,
                    data.status_count.absent || 0,
                    data.status_count.late || 0,
                    data.status_count.excused || 0
                ],
                backgroundColor: [
                    '#48bb78',
                    '#f56565',
                    '#ed8936',
                    '#4299e1'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function renderTeacherChart(data) {
    const ctx = document.getElementById('teacher-attendance-chart');
    if (!ctx) return;
    
    const dailyData = Object.entries(data.daily_stats || {});
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: dailyData.map(([date]) => date),
            datasets: [{
                label: '出席人數',
                data: dailyData.map(([, stats]) => stats.status_count.present || 0),
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function renderAdminChart(data) {
    const ctx = document.getElementById('admin-overview-chart');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['用戶', '課程', '表單', '記錄'],
            datasets: [{
                label: '數量',
                data: [
                    data.basic_stats.total_users,
                    data.basic_stats.total_courses,
                    data.basic_stats.total_forms,
                    data.basic_stats.total_records
                ],
                backgroundColor: [
                    '#667eea',
                    '#764ba2',
                    '#48bb78',
                    '#ed8936'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// 模態框功能
function showModal(title, content) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = content;
    document.getElementById('modal').classList.add('show');
}

function closeModal() {
    document.getElementById('modal').classList.remove('show');
}

// 通知系統
function showNotification(title, message, type = 'info') {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');
    
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="${icons[type]} notification-icon"></i>
            <div class="notification-text">
                <div class="notification-title">${title}</div>
                <div class="notification-message">${message}</div>
            </div>
        </div>
    `;
    
    container.appendChild(notification);
    
    // 自動移除通知
    setTimeout(() => {
        notification.style.animation = 'slideInRight 0.3s ease reverse';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

// 工具函數
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-TW');
}

function formatTime(timeString) {
    return timeString.substring(0, 5);
}



// 查看課程學生名單
async function viewCourseStudents(courseId) {
    try {
        const response = await fetch(`/api/courses/${courseId}/students`);
        if (response.ok) {
            const data = await response.json();
            displayStudentList(data);
        } else {
            const error = await response.json();
            showNotification('錯誤', error.error || '無法載入學生名單', 'error');
        }
    } catch (error) {
        console.error('載入學生名單失敗:', error);
        showNotification('錯誤', '網路連線錯誤', 'error');
    }
}

// 顯示學生名單模態框
function displayStudentList(data) {
    const studentsHtml = data.students.map(student => `
        <div class="student-item">
            <div class="student-info">
                <div class="student-name">${student.full_name}</div>
                <div class="student-id">學號: ${student.student_id}</div>
                <div class="student-email">${student.email}</div>
                <div class="join-date">加入時間: ${formatDate(student.enrolled_at)}</div>
            </div>
            <div class="student-stats">
                <div class="stat-item">
                    <span class="stat-label">出席率:</span>
                    <span class="stat-value good">85%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">已填表單:</span>
                    <span class="stat-value">8/10</span>
                </div>
            </div>
        </div>
    `).join('');

    showModal(`${data.course.course_name} - 學生名單 (${data.total_students}人)`, `
        <div class="student-list-container">
            ${data.students.length > 0 ? studentsHtml : `
                <div class="empty-state">
                    <i class="fas fa-users"></i>
                    <h3>尚無學生加入</h3>
                    <p>請將課程加入代碼分享給學生</p>
                </div>
            `}
        </div>
        <style>
            .student-list-container {
                max-height: 60vh;
                overflow-y: auto;
            }
            .student-item {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                padding: 1rem;
                border: 1px solid var(--border-color);
                border-radius: var(--border-radius-sm);
                margin-bottom: 1rem;
                background: var(--bg-color);
            }
            .student-info {
                flex: 1;
            }
            .student-name {
                font-weight: 600;
                font-size: 1.1rem;
                margin-bottom: 0.25rem;
            }
            .student-id, .student-email, .join-date {
                color: var(--text-secondary);
                font-size: 0.875rem;
                margin-bottom: 0.25rem;
            }
            .student-stats {
                text-align: right;
                min-width: 150px;
            }
            .stat-item {
                margin-bottom: 0.5rem;
            }
            .stat-label {
                color: var(--text-secondary);
                font-size: 0.875rem;
            }
            .stat-value {
                font-weight: 600;
                margin-left: 0.5rem;
            }
            .stat-value.good { color: var(--success-color); }
            .stat-value.warning { color: var(--warning-color); }
            .stat-value.poor { color: var(--error-color); }
        </style>
    `);
}

// 編輯課程
async function editCourse(courseId) {
    try {
        // 先獲取課程資訊
        const response = await fetch(`/api/courses/${courseId}`);
        if (response.ok) {
            const course = await response.json();
            showEditCourseModal(course);
        } else {
            const error = await response.json();
            showNotification('錯誤', error.error || '無法載入課程資訊', 'error');
        }
    } catch (error) {
        console.error('載入課程資訊失敗:', error);
        showNotification('錯誤', '網路連線錯誤', 'error');
    }
}

// 顯示編輯課程模態框
function showEditCourseModal(course) {
    showModal('編輯課程', `
        <form id="edit-course-form" onsubmit="updateCourse(event, ${course.id})">
            <div class="form-group">
                <label for="edit-course-code">課程代碼</label>
                <div class="input-group">
                    <i class="fas fa-code"></i>
                    <input type="text" id="edit-course-code" name="course_code" value="${course.course_code}" required>
                </div>
            </div>
            <div class="form-group">
                <label for="edit-course-name">課程名稱</label>
                <div class="input-group">
                    <i class="fas fa-book"></i>
                    <input type="text" id="edit-course-name" name="course_name" value="${course.course_name}" required>
                </div>
            </div>
            <div class="form-group">
                <label for="edit-course-description">課程描述</label>
                <div class="input-group">
                    <i class="fas fa-align-left"></i>
                    <input type="text" id="edit-course-description" name="description" value="${course.description || ''}" placeholder="選填">
                </div>
            </div>
            <div class="form-group">
                <label>課程加入代碼</label>
                <div class="input-group">
                    <i class="fas fa-key"></i>
                    <input type="text" value="${course.join_code}" readonly style="background: var(--bg-color); color: var(--text-secondary);">
                </div>
                <small style="color: var(--text-secondary); font-size: 0.75rem;">加入代碼無法修改</small>
            </div>
            <button type="submit" class="btn btn-primary btn-full">
                <i class="fas fa-save"></i> 更新課程
            </button>
        </form>
    `);
}

// 更新課程
async function updateCourse(e, courseId) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const courseData = {
        course_code: formData.get('course_code'),
        course_name: formData.get('course_name'),
        description: formData.get('description') || ''
    };
    
    try {
        const response = await fetch(`/api/courses/${courseId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(courseData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('成功', '課程更新成功', 'success');
            closeModal();
            await loadTeacherCourses();
        } else {
            showNotification('失敗', result.error, 'error');
        }
    } catch (error) {
        console.error('更新課程失敗:', error);
        showNotification('錯誤', '網路連線錯誤', 'error');
    }
}

// 查看課程詳情
async function viewCourseDetails(courseId) {
    try {
        const response = await fetch(`/api/courses/${courseId}`);
        if (response.ok) {
            const course = await response.json();
            showCourseDetailsModal(course);
        } else {
            const error = await response.json();
            showNotification('錯誤', error.error || '無法載入課程詳情', 'error');
        }
    } catch (error) {
        console.error('載入課程詳情失敗:', error);
        showNotification('錯誤', '網路連線錯誤', 'error');
    }
}

// 顯示課程詳情模態框
function showCourseDetailsModal(course) {
    showModal('課程詳情', `
        <div class="course-details">
            <div class="detail-item">
                <label>課程代碼:</label>
                <span>${course.course_code}</span>
            </div>
            <div class="detail-item">
                <label>課程名稱:</label>
                <span>${course.course_name}</span>
            </div>
            <div class="detail-item">
                <label>授課老師:</label>
                <span>${course.teacher_name || '未知'}</span>
            </div>
            <div class="detail-item">
                <label>課程描述:</label>
                <span>${course.description || '無描述'}</span>
            </div>
            <div class="detail-item">
                <label>建立時間:</label>
                <span>${formatDate(course.created_at)}</span>
            </div>
            ${course.join_code ? `
                <div class="detail-item">
                    <label>加入代碼:</label>
                    <span class="join-code-display">${course.join_code}</span>
                </div>
            ` : ''}
            ${course.student_count !== undefined ? `
                <div class="detail-item">
                    <label>學生人數:</label>
                    <span>${course.student_count} 人</span>
                </div>
            ` : ''}
        </div>
        <style>
            .course-details {
                display: flex;
                flex-direction: column;
                gap: 1rem;
            }
            .detail-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.75rem;
                background: var(--bg-color);
                border-radius: var(--border-radius-sm);
                border: 1px solid var(--border-color);
            }
            .detail-item label {
                font-weight: 600;
                color: var(--text-primary);
            }
            .detail-item span {
                color: var(--text-secondary);
            }
            .join-code-display {
                font-family: 'Courier New', monospace;
                background: var(--primary-color);
                color: white;
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
                font-weight: 600;
                letter-spacing: 1px;
            }
        </style>
    `);
}

// 增強的圖表渲染功能
function renderTeacherChart(data) {
    const ctx = document.getElementById('teacher-attendance-chart');
    if (!ctx) return;
    
    // 如果已有圖表，先銷毀
    if (window.teacherChart) {
        window.teacherChart.destroy();
    }
    
    // 準備多種圖表數據
    const dailyData = Object.entries(data.daily_stats || {});
    const studentData = Object.entries(data.student_stats || {});
    
    // 創建多個圖表選項
    const chartConfigs = {
        daily: {
            type: 'line',
            data: {
                labels: dailyData.map(([date]) => date),
                datasets: [{
                    label: '出席人數',
                    data: dailyData.map(([, stats]) => stats.status_count?.present || 0),
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: '缺席人數',
                    data: dailyData.map(([, stats]) => stats.status_count?.absent || 0),
                    borderColor: '#f56565',
                    backgroundColor: 'rgba(245, 101, 101, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '每日出缺席趨勢'
                    },
                    legend: {
                        position: 'bottom'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        },
        status: {
            type: 'doughnut',
            data: {
                labels: ['出席', '缺席', '遲到', '請假'],
                datasets: [{
                    data: [
                        data.status_count?.present || 0,
                        data.status_count?.absent || 0,
                        data.status_count?.late || 0,
                        data.status_count?.excused || 0
                    ],
                    backgroundColor: [
                        '#48bb78',
                        '#f56565',
                        '#ed8936',
                        '#4299e1'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '出缺席狀態分布'
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        },
        students: {
            type: 'bar',
            data: {
                labels: studentData.slice(0, 10).map(([name]) => name.split(' - ')[1] || name),
                datasets: [{
                    label: '出席次數',
                    data: studentData.slice(0, 10).map(([, stats]) => stats.status_count?.present || 0),
                    backgroundColor: '#48bb78'
                }, {
                    label: '缺席次數',
                    data: studentData.slice(0, 10).map(([, stats]) => stats.status_count?.absent || 0),
                    backgroundColor: '#f56565'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '學生出缺席統計 (前10名)'
                    },
                    legend: {
                        position: 'bottom'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        }
    };
    
    // 預設顯示每日趨勢圖
    window.teacherChart = new Chart(ctx, chartConfigs.daily);
    
    // 添加圖表切換按鈕
    const chartContainer = ctx.parentElement;
    if (!chartContainer.querySelector('.chart-controls')) {
        const controls = document.createElement('div');
        controls.className = 'chart-controls';
        controls.innerHTML = `
            <div class="chart-buttons">
                <button class="chart-btn active" onclick="switchTeacherChart('daily')">每日趨勢</button>
                <button class="chart-btn" onclick="switchTeacherChart('status')">狀態分布</button>
                <button class="chart-btn" onclick="switchTeacherChart('students')">學生統計</button>
            </div>
            <style>
                .chart-controls {
                    margin-bottom: 1rem;
                    text-align: center;
                }
                .chart-buttons {
                    display: inline-flex;
                    background: var(--border-color);
                    border-radius: var(--border-radius-sm);
                    padding: 0.25rem;
                }
                .chart-btn {
                    background: none;
                    border: none;
                    padding: 0.5rem 1rem;
                    border-radius: var(--border-radius-sm);
                    cursor: pointer;
                    transition: var(--transition);
                    font-size: 0.875rem;
                    color: var(--text-secondary);
                }
                .chart-btn:hover {
                    background: var(--surface-color);
                    color: var(--text-primary);
                }
                .chart-btn.active {
                    background: var(--primary-color);
                    color: white;
                }
            </style>
        `;
        chartContainer.insertBefore(controls, ctx);
    }
    
    // 存儲圖表配置供切換使用
    window.teacherChartConfigs = chartConfigs;
}

// 切換老師圖表
function switchTeacherChart(type) {
    if (!window.teacherChart || !window.teacherChartConfigs) return;
    
    // 更新按鈕狀態
    document.querySelectorAll('.chart-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // 銷毀舊圖表並創建新圖表
    window.teacherChart.destroy();
    const ctx = document.getElementById('teacher-attendance-chart');
    window.teacherChart = new Chart(ctx, window.teacherChartConfigs[type]);
}

