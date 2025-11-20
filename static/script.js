
document.getElementById('n').addEventListener('input', generateMatrices);
document.getElementById('m').addEventListener('input', generateMatrices);

function generateMatrices() {
    const n = parseInt(document.getElementById('n').value) || 0;
    const m = parseInt(document.getElementById('m').value) || 0;
    
    // Allocation Matrix
    let allocationMatrix = '';
    for (let i = 0; i < n; i++) {
        allocationMatrix += '<div class="row"><label>Process ' + (i)   + ':</label> ';
        for (let j = 0; j < m; j++) {
            allocationMatrix += '<input type="number" name="alloc_' + i + '_' + j + '" min="0" required> ';
        }
        allocationMatrix += '</div>';
    }
    document.getElementById('allocation-matrix').innerHTML = allocationMatrix;
    
    // Request Matrix
    let reqquestMatrix = '';
    for (let i = 0; i < n; i++) {
        reqquestMatrix += '<div class="row"><label>Process ' + (i) + ':</label> ';
        for (let j = 0; j < m; j++) {
            reqquestMatrix += '<input type="number" name="req_' + i + '_' + j + '" min="0" required> ';
        }
        reqquestMatrix += '</div>';
    }
    document.getElementById('request-matrix').innerHTML = reqquestMatrix;
    
    // Available Resources
    let availableMatrix = '';
    for (let j = 0; j < m; j++) {
        availableMatrix += '<input type="number" name="avail_' + j + '" min="0" required> ';
    }
    document.getElementById('available-resources').innerHTML = availableMatrix;
}
