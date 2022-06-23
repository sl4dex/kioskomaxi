from website.models.product import Product
from website.models.movements import Movements
from website.models.branch import Branch
from website.models.inventory import Inventory
from flask_login import login_required
from flask import Blueprint, render_template, request, flash, redirect, jsonify, abort, url_for
from flask_login import login_required, current_user
from sqlalchemy import and_

inventory = Blueprint('inventory', __name__)

@login_required
@inventory.route('/inventory', methods=['GET', 'POST'], strict_slashes=False)
def inventory_page():
    """inventory page"""

    #if user is not confirmed, block access and send to home
    if current_user.confirmed is False:
        flash('Please confirm your account, check your email (and spam folder)', 'error')
        return redirect(url_for('views.home'))

    graph_data = {'Task' : 'Products per branch'}

    formDict = request.form.to_dict()

    # store some  product name if some product is searched
    search = formDict.get('search')
    search = search.lower().strip() if search else None

    # consulting stock from all branches
    stockQuery = Inventory.query.filter_by(owner=current_user.email).all()
    stock = []
    # filling stock dictionary with prod name, quantity, description and product id
    for item in stockQuery:
        stockItem = {}
        product = Product.query.filter_by(owner=current_user.email).filter_by(id=item.prod_id).first()
        # if search not in product name then its not listed
        if search and search not in product.name.lower():
            continue
        stockItem['name'] = product.name
        stockItem['quantity'] = item.quantity
        stockItem['branch'] = "All Branches"
        stockItem['description'] = product.description
        stockItem['id'] = item.prod_id
        stockItem['qr_barcode'] = product.qr_barcode

        stock.append(stockItem)
        
        graph_data[product.name] = item.quantity
    if search and not stock:
        flash("No items with that name", "error")
        return redirect('/inventory')

    # if user presses Search
    if request.method == 'POST' and "btn-srch" in request.form:

        selectedBranch = formDict.get('selectBranch')

        # filtering by branch
        if selectedBranch != 'All Branches (default)':
            selectedBranch = Branch.query.filter_by(owner=current_user.email).filter_by(name=selectedBranch).first()
            for item in stock:
                # calculating the current stock for specific branch
                currentStock = 0
                for mov in Movements.query.filter_by(owner=current_user.email).filter(and_(
                                                                                      Movements.prod_id == item['id'],
                                                                                      Movements.branch_id == selectedBranch.id)).all():
                    if mov.in_out is True:
                        currentStock += mov.quantity
                    elif mov.in_out is False:
                        currentStock -= mov.quantity
                item['quantity'] = currentStock
                item['branch'] = selectedBranch.name
                graph_data[item['name']] = item['quantity']
                print(item)         

        if selectedBranch == 'All Branches (default)' and search:
            for selectedBranch in Branch.query.filter_by(owner=current_user.email).all():
                for item in stock:
                    # calculating the current stock for all branches
                    currentStock = 0
                    for mov in Movements.query.filter_by(owner=current_user.email).filter(and_(Movements.prod_id == item['id'],
                                                        Movements.branch_id == selectedBranch.id)).all():
                        if mov.in_out is True:
                            currentStock += mov.quantity
                        elif mov.in_out is False:
                            currentStock -= mov.quantity
                    if item['name'] == search:
                        graph_data[item['name'] + " " + "On(" + selectedBranch.name + ")"] = currentStock
                        if item['name'] in graph_data:
                            graph_data.pop(item['name'])
                        print(graph_data)
                    print(item)

    # branches from user to pass to jinja
    branches = Branch.query.filter_by(owner=current_user.email).all()
    branchesList = ["All Branches (default)"]
    for branch in branches:
        branchesList.append(branch.name)

    return render_template('inventory.html', stock=stock, user=current_user, branches=branchesList, data=graph_data)


@login_required
@inventory.route('/inventory/<id>', methods=['GET'], strict_slashes=False)
def inventory_product(id):
    """Api Endpoint for inventory product"""

    # if user is not confirmed, block access and send to home
    if current_user.confirmed is False:
        flash('Please confirm your account, check your email (and spam folder)', 'error')
        return redirect(url_for('views.home'))
    
    # consulting stock from all branches
    stockQuery = Inventory.query.filter_by(owner=current_user.email).filter_by(prod_id=id).first()


    #filling stock dictionary with prod name, quantity, description and product id
    stockItem = {}

    product = Product.query.filter_by(owner=current_user.email).filter_by(id=id).first()
        
    # if is searched a particular product only that product is gonna be listed

    stockItem['name'] = product.name
    stockItem['quantity'] = stockQuery.quantity
    stockItem['branch'] = "All Branches"
    stockItem['description'] = product.description
    stockItem['id'] = stockQuery.prod_id
    stockItem['qr_barcode'] = product.qr_barcode

    if not stockItem:
        return None

    return jsonify(stockItem)